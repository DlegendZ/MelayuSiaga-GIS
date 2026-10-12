"""Prepare validated metric inputs and the exact buffered network bbox using QGIS Python."""

import argparse
import hashlib
import os
import sys
import uuid
from pathlib import Path

try:
    from ._common import ROOT, read_csv, write_json
except ImportError:
    from _common import ROOT, read_csv, write_json

from km_flood_priority.core.normalize import parse_rw
from km_flood_priority.core.schema import SAFE_POINT_COLUMNS
from km_flood_priority.core.validation import require_columns


def latest(folder, pattern):
    paths = sorted((ROOT / folder).glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No {pattern} in {folder}; acquire the real source first")
    return paths[-1]


def initialize_qgis(prefix=None):
    try:
        from qgis.core import QgsApplication
    except ImportError as error:
        raise RuntimeError(
            "QGIS bindings are unavailable. Use QGIS/OSGeo4W Python or a QGIS Docker container; "
            "the ordinary development .venv cannot create the GeoPackage."
        ) from error
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if prefix:
        QgsApplication.setPrefixPath(str(prefix), True)
    application = QgsApplication([], False)
    application.initQgis()
    plugin_path = Path(QgsApplication.pkgDataPath()) / "python/plugins"
    if str(plugin_path) not in sys.path:
        sys.path.insert(0, str(plugin_path))
    from processing.core.Processing import Processing

    Processing.initialize()
    return application


def load_metric(path, name, *, repair=False):
    import processing
    from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer

    layer = QgsVectorLayer(str(path), name, "ogr")
    if not layer.isValid() or not layer.crs().isValid():
        raise ValueError(f"Invalid layer or missing CRS: {path}")
    layer = processing.run(
        "native:reprojectlayer",
        {
            "INPUT": layer,
            "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:32748"),
            "OUTPUT": "memory:",
        },
    )["OUTPUT"]
    if repair:
        layer = processing.run(
            "native:fixgeometries",
            {
                "INPUT": layer,
                "OUTPUT": "memory:",
            },
        )["OUTPUT"]
    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom.isEmpty() or not geom.isGeosValid():
            raise ValueError(f"{path}: invalid/empty geometry remains after preparation")
    layer.setName(name)
    return layer


def validate_boundaries(rw, boundary):
    from qgis.core import QgsGeometry

    numbers = []
    for feature in rw.getFeatures():
        values = parse_rw(str(feature["wadmrw"]))
        if len(values) != 1:
            raise ValueError("Official RW field must identify exactly one RW per polygon")
        numbers.extend(values)
    if not numbers or len(numbers) != len(set(numbers)):
        raise ValueError("At least one RW and unique RW numbers are required")
    rw_union = QgsGeometry.unaryUnion([f.geometry() for f in rw.getFeatures()])
    kel_union = QgsGeometry.unaryUnion([f.geometry() for f in boundary.getFeatures()])
    if rw_union.isEmpty() or kel_union.isEmpty() or kel_union.area() <= 0:
        raise ValueError("Administrative dissolve produced empty geometry")
    ratio = rw_union.area() / kel_union.area()
    if abs(ratio - 1) > 0.05:
        raise ValueError(
            f"Dissolved RW/boundary area ratio {ratio:.4f} exceeds ±5%; inspect sources"
        )
    hectares = kel_union.area() / 10000
    area_warning = abs(hectares / 47.83 - 1) > 0.15
    if area_warning:
        print(f"WARNING: boundary area {hectares:.2f} ha differs from recorded 47.83 ha by >15%")
    return kel_union, {
        "rw_numbers": sorted(numbers),
        "rw_count": len(numbers),
        "kelurahan_area_ha": hectares,
        "dissolved_rw_area_ha": rw_union.area() / 10000,
        "rw_kelurahan_area_ratio": ratio,
        "reference_area_warning": area_warning,
        "all_geometries_valid": True,
    }


def buffer_and_bbox(kel_union):
    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsFeature,
        QgsGeometry,
        QgsProject,
        QgsVectorLayer,
    )

    buffered = kel_union.buffer(1000, 24)
    if buffered.isEmpty() or not buffered.isGeosValid():
        raise ValueError("1000 m network context buffer is invalid")
    geographic = QgsGeometry(buffered)
    geographic.transform(
        QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:32748"),
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsProject.instance().transformContext(),
        )
    )
    box = geographic.boundingBox()
    buffered.convertToMultiType()
    layer = QgsVectorLayer("MultiPolygon?crs=EPSG:32748", "network_context", "memory")
    feature = QgsFeature()
    feature.setGeometry(buffered)
    if not layer.dataProvider().addFeatures([feature])[0]:
        raise ValueError("Could not create the network buffer layer")
    layer.updateExtents()
    return layer, [box.yMinimum(), box.xMinimum(), box.yMaximum(), box.xMaximum()]


def safe_points_layer(path):
    import math

    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsFeature,
        QgsField,
        QgsGeometry,
        QgsPointXY,
        QgsProject,
        QgsVectorLayer,
    )
    from qgis.PyQt.QtCore import QMetaType

    layer = QgsVectorLayer("Point?crs=EPSG:32748", "safe_points", "memory")
    provider = layer.dataProvider()
    fields = [
        QgsField(
            column,
            QMetaType.Type.Int
            if column == "capacity"
            else QMetaType.Type.Double
            if column in {"lon", "lat"}
            else QMetaType.Type.QString,
        )
        for column in SAFE_POINT_COLUMNS
    ]
    provider.addAttributes(fields)
    layer.updateFields()
    if path is None:
        return layer
    headers, rows = read_csv(path)
    require_columns(headers, SAFE_POINT_COLUMNS)
    transform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"),
        QgsCoordinateReferenceSystem("EPSG:32748"),
        QgsProject.instance().transformContext(),
    )
    identifiers, features = set(), []
    for row in rows:
        lon, lat = float(row["lon"]), float(row["lat"])
        if not (
            math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90
        ):
            raise ValueError(f"Safe point {row['sp_id']}: invalid lon/lat")
        if not row["sp_id"] or row["sp_id"] in identifiers or row["verified"] not in {"Y", "N"}:
            raise ValueError("Safe points require unique non-empty IDs and verified=Y/N")
        identifiers.add(row["sp_id"])
        if row["verified"] == "Y" and not (row["source_id"] and row["source_ref"]):
            raise ValueError(f"Verified safe point {row['sp_id']} lacks a cited source")
        capacity = int(row["capacity"]) if row["capacity"] else None
        if capacity is not None and capacity < 0:
            raise ValueError("Safe-point capacity cannot be negative")
        attributes = {**row, "capacity": capacity, "lon": lon, "lat": lat}
        feature = QgsFeature(layer.fields())
        feature.setAttributes([attributes[column] for column in SAFE_POINT_COLUMNS])
        feature.setGeometry(QgsGeometry.fromPointXY(transform.transform(QgsPointXY(lon, lat))))
        features.append(feature)
    if not provider.addFeatures(features)[0]:
        raise ValueError("Failed to build the safe-point layer")
    layer.updateExtents()
    return layer


def save_package(layers, output):
    from qgis.core import QgsProject, QgsVectorFileWriter

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".inputs-{uuid.uuid4().hex}.gpkg")
    for index, (name, layer) in enumerate(layers.items()):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName, options.layerName, options.fileEncoding = "GPKG", name, "UTF-8"
        options.actionOnExistingFile = (
            QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
            if index == 0
            else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
        )
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            str(temporary),
            QgsProject.instance().transformContext(),
            options,
        )
        if result[0] != QgsVectorFileWriter.WriterError.NoError:
            raise ValueError(
                f"Writing {name} failed: {result[1]}; partial file retained at {temporary}"
            )
    os.replace(temporary, output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rw", type=Path)
    parser.add_argument("--kelurahan", type=Path)
    parser.add_argument("--roads", type=Path)
    parser.add_argument("--buildings", type=Path)
    parser.add_argument("--safe-points", type=Path)
    parser.add_argument("--qgis-prefix", type=Path)
    parser.add_argument("--prepare-bbox-only", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/inputs.gpkg")
    parser.add_argument(
        "--overwrite", action="store_true", help="Explicitly confirm replacing generated output"
    )
    args = parser.parse_args(argv)
    rw_path = args.rw or latest("data/raw/admin", "rw_kampung_melayu_*.geojson")
    kel_path = args.kelurahan or latest("data/raw/admin", "kelurahan_kampung_melayu_*.geojson")
    if args.output.exists() and not args.overwrite and not args.prepare_bbox_only:
        parser.error("Output exists. Review it before explicitly confirming --overwrite.")
    application = initialize_qgis(args.qgis_prefix)
    try:
        import processing

        rw = load_metric(rw_path, "rw", repair=True)
        kel = load_metric(kel_path, "kelurahan_boundary", repair=True)
        kel_union, report = validate_boundaries(rw, kel)
        buffer_layer, bbox = buffer_and_bbox(kel_union)
        write_json(
            ROOT / "data/interim/network_bbox.json",
            {
                "bbox_4326": bbox,
                "buffer_m": 1000,
                "source_boundary": str(kel_path.resolve()),
                "boundary_sha256": hashlib.sha256(kel_path.read_bytes()).hexdigest(),
                "method": "EPSG:32748 buffer(1000,24); transformed geometry bbox in EPSG:4326",
            },
        )
        if args.prepare_bbox_only:
            write_json(ROOT / "data/interim/boundary_validation.json", report)
            print(f"Boundary validation passed; {report['rw_count']} RW; network bbox={bbox}")
            return 0
        roads_path = args.roads or latest("data/raw/osm", "roads_*.geojson")
        buildings_path = args.buildings or latest("data/raw/osm", "buildings_*.geojson")
        layers = {
            "rw": processing.run(
                "native:clip",
                {
                    "INPUT": rw,
                    "OVERLAY": kel,
                    "OUTPUT": "memory:",
                },
            )["OUTPUT"],
            "kelurahan_boundary": kel,
        }
        for name, path in (("roads", roads_path), ("buildings", buildings_path)):
            prepared = load_metric(path, name, repair=name == "buildings")
            layers[name] = processing.run(
                "native:clip",
                {
                    "INPUT": prepared,
                    "OVERLAY": buffer_layer,
                    "OUTPUT": "memory:",
                },
            )["OUTPUT"]
        if layers["rw"].featureCount() != report["rw_count"] or layers["roads"].featureCount() == 0:
            raise ValueError("Clipping removed RW units or left no usable network roads")
        safe_path = args.safe_points
        if safe_path is None:
            options = [
                ROOT / "data/clean/safe_points.csv",
                ROOT / "data/interim/safe_point_candidates_osm.csv",
            ]
            safe_path = next((path for path in options if path.exists()), None)
        layers["safe_points"] = safe_points_layer(safe_path)
        for name, layer in layers.items():
            if layer.crs().authid() != "EPSG:32748":
                raise ValueError(f"{name}: output CRS must be EPSG:32748")
            for feature in layer.getFeatures():
                geometry = feature.geometry()
                if geometry.isEmpty() or not geometry.isGeosValid():
                    raise ValueError(f"{name}: invalid/empty geometry after clipping")
        save_package(layers, args.output)
        report.update(
            {
                "crs": "EPSG:32748",
                "feature_counts": {name: layer.featureCount() for name, layer in layers.items()},
                "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "source_files": [
                    str(path.resolve()) for path in (rw_path, kel_path, roads_path, buildings_path)
                ],
            }
        )
        write_json(args.output.with_suffix(".validation.json"), report)
        print(f"Saved {args.output}; layers={report['feature_counts']}")
        return 0
    finally:
        application.exitQgis()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(f"build_inputs: {error}")

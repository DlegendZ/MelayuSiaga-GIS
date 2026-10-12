"""Local CSV and vector adapters; all spatial computation uses EPSG:32748."""

import csv
from dataclasses import asdict
from datetime import date
from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureSink,
    QgsGeometry,
    QgsProcessingException,
    QgsVariantUtils,
    QgsVectorLayer,
)

from ..core.normalize import parse_date, parse_rw
from ..core.schema import (
    CLOSURE_COLUMNS,
    SAFE_POINT_COLUMNS,
    SOURCE_COLUMNS,
    AccessRecord,
    Closure,
    Event,
    Origin,
    Road,
    SafePoint,
)
from ..core.validation import require_columns
from .fields import attributes, make_fields

METRIC_CRS = QgsCoordinateReferenceSystem("EPSG:32748")


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader, [])
        if headers:
            headers[0] = headers[0].lstrip("\ufeff")
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path}: duplicate CSV column names")
        rows = []
        for values in reader:
            if not values or values[0].lstrip().startswith("#"):
                continue
            if len(values) != len(headers):
                raise ValueError(f"{path}, line {reader.line_num}: incorrect CSV value count")
            rows.append(dict(zip(headers, values, strict=True)))
    return headers, rows


def read_sources(path):
    headers, rows = read_csv(path)
    require_columns(headers, SOURCE_COLUMNS)
    identifiers = [row["source_id"].strip() for row in rows]
    if any(not identifier for identifier in identifiers) or len(identifiers) != len(
        set(identifiers)
    ):
        raise ValueError("Sources require unique, non-empty source_id values")
    return rows


def value(feature, name):
    item = feature[name]
    return None if item is None or QgsVariantUtils.isNull(item) else item


def require_fields(source, names):
    if source is None:
        raise ValueError("Required input layer could not be loaded")
    require_columns(source.fields().names(), names)


def metric_geometry(feature, source, context):
    if not source.sourceCrs().isValid():
        raise ValueError("Input layer has no valid CRS; assign its true source CRS before running")
    geometry = QgsGeometry(feature.geometry())
    if geometry.isEmpty() or not geometry.isGeosValid():
        raise ValueError(f"Feature {feature.id()}: empty/invalid geometry; repair the input first")
    if source.sourceCrs() != METRIC_CRS:
        geometry.transform(
            QgsCoordinateTransform(source.sourceCrs(), METRIC_CRS, context.transformContext())
        )
    return geometry


def rw_units(source, field, context):
    require_fields(source, [field])
    result = {}
    for feature in source.getFeatures():
        numbers = parse_rw(str(value(feature, field) or ""))
        if len(numbers) != 1 or numbers[0] <= 0 or numbers[0] in result:
            raise ValueError("Each RW polygon must have one unique positive RW number")
        geometry = metric_geometry(feature, source, context)
        geometry.convertToMultiType()
        result[numbers[0]] = geometry
    if not result:
        raise ValueError("RW_LAYER contains no analysis units")
    return result


def origins_from_units(units):
    origins = []
    for number, geometry in sorted(units.items()):
        point = geometry.pointOnSurface().asPoint()
        origins.append(Origin(number, (point.x(), point.y())))
    return origins


def roads_from_source(source, context):
    require_fields(source, ["osm_id", "highway", "name"])
    roads = []
    for feature in source.getFeatures():
        geometry = metric_geometry(feature, source, context)
        lines = geometry.asMultiPolyline() if geometry.isMultipart() else [geometry.asPolyline()]
        for line in lines:
            roads.append(
                Road(
                    str(value(feature, "osm_id")),
                    tuple((point.x(), point.y()) for point in line),
                    str(value(feature, "highway") or ""),
                    str(value(feature, "name") or ""),
                )
            )
    return roads


def targets_from_source(source, context):
    if source is None:
        return []
    require_fields(source, SAFE_POINT_COLUMNS)
    points, identifiers = [], set()
    for feature in source.getFeatures():
        identifier, verified = (
            str(value(feature, "sp_id") or ""),
            str(value(feature, "verified") or ""),
        )
        if not identifier or identifier in identifiers or verified not in {"Y", "N"}:
            raise ValueError("Safe points require unique non-empty sp_id and verified=Y/N")
        if verified == "Y" and not (value(feature, "source_id") and value(feature, "source_ref")):
            raise ValueError(f"Verified safe point {identifier} must cite source_id and source_ref")
        identifiers.add(identifier)
        geometry = metric_geometry(feature, source, context)
        if geometry.isMultipart():
            raise ValueError("Safe points must be individual point features")
        point = geometry.asPoint()
        name = str(value(feature, "name") or "") if "name" in source.fields().names() else ""
        points.append(SafePoint(identifier, (point.x(), point.y()), verified, name))
    return points


def read_closures(path):
    if not path:
        return []
    headers, rows = read_csv(path)
    require_columns(headers, CLOSURE_COLUMNS)
    result, identifiers = [], set()
    for row in rows:
        if (
            not row["closure_id"]
            or row["closure_id"] in identifiers
            or not row["road_ref"]
            or row["road_ref_type"] not in {"OSM_ID", "NAME"}
            or row["verified"] not in {"Y", "N"}
        ):
            raise ValueError("Closures require unique IDs, road_ref, OSM_ID/NAME and verified=Y/N")
        if row["verified"] == "Y" and not (row["source_id"] and row["source_ref"]):
            raise ValueError("Verified closures must cite a source_id and source_ref")
        identifiers.add(row["closure_id"])
        result.append(Closure(**{**row, "event_date": parse_date(row["event_date"])}))
    return result


def event_dates(text, closures):
    if text.strip().upper() == "ALL":
        return sorted({closure.event_date for closure in closures})
    return sorted({parse_date(item.strip()) for item in text.split(",") if item.strip()})


def rows_from_source(source):
    return [
        {field.name(): value(feature, field.name()) for field in source.fields()}
        for feature in source.getFeatures()
    ]


def date_value(item):
    if isinstance(item, date):
        return item
    if hasattr(item, "toPyDate"):
        return item.toPyDate()
    return parse_date(str(item))


def events_from_source(source):
    require_fields(source, ["event_uid", "event_date", "rw_no", "duplicate_of", "source_id"])
    events = []
    for row in rows_from_source(source):
        data = {name: row[name] for name in Event.__dataclass_fields__ if name in row}
        data["event_date"] = date_value(data["event_date"])
        events.append(Event(**data))
    return events


def access_from_source(source):
    if source is None:
        return None
    require_fields(source, AccessRecord.__dataclass_fields__)
    return [
        AccessRecord(**{name: row[name] for name in AccessRecord.__dataclass_fields__})
        for row in rows_from_source(source)
    ]


def make_layer(name, geometry_type, specification, records=(), geometries=None):
    layer = QgsVectorLayer(
        geometry_type + ("?crs=EPSG:32748" if geometry_type != "None" else ""), name, "memory"
    )
    layer.dataProvider().addAttributes(make_fields(specification).toList())
    layer.updateFields()
    features = []
    for index, record in enumerate(records):
        feature = QgsFeature(layer.fields())
        feature.setAttributes(attributes(record, layer.fields()))
        if geometries is not None:
            feature.setGeometry(geometries[index])
        features.append(feature)
    if features and not layer.dataProvider().addFeatures(features)[0]:
        raise ValueError(f"Could not create {name} features")
    layer.updateExtents()
    layer.setCustomProperty("skipMemoryLayersCheck", 1)
    return layer


def metric_copy(source, name, context):
    from qgis.core import QgsWkbTypes

    layer = QgsVectorLayer(
        QgsWkbTypes.displayString(source.wkbType()) + "?crs=EPSG:32748", name, "memory"
    )
    layer.dataProvider().addAttributes(source.fields().toList())
    layer.updateFields()
    features = []
    for original in source.getFeatures():
        feature = QgsFeature(layer.fields())
        feature.setAttributes(original.attributes())
        feature.setGeometry(metric_geometry(original, source, context))
        features.append(feature)
    if features and not layer.dataProvider().addFeatures(features)[0]:
        raise ValueError(f"Could not copy metric {name} layer")
    layer.updateExtents()
    return layer


def table_copy(source, name):
    layer = QgsVectorLayer("None", name, "memory")
    layer.dataProvider().addAttributes(source.fields().toList())
    layer.updateFields()
    features = []
    for original in source.getFeatures():
        feature = QgsFeature(layer.fields())
        feature.setAttributes(original.attributes())
        features.append(feature)
    if features and not layer.dataProvider().addFeatures(features)[0]:
        raise ValueError(f"Could not copy {name} table")
    return layer


def output_layer(algorithm, parameters, key, context, layer, feedback):
    sink, destination = algorithm.parameterAsSink(
        parameters, key, context, layer.fields(), layer.wkbType(), layer.crs()
    )
    if sink is None:
        raise QgsProcessingException(f"Could not create {key}")
    for feature in layer.getFeatures():
        if feedback.isCanceled():
            raise QgsProcessingException("Processing canceled")
        if not sink.addFeature(feature, QgsFeatureSink.Flag.FastInsert):
            raise QgsProcessingException(f"Could not write feature to {key}")
    sink.finalize()
    return destination


def event_records(events, raw_rows):
    notes = {(row["source_id"], row["event_id"]): row.get("notes", "") for row in raw_rows}
    return [
        {
            **asdict(event),
            "year": event.year,
            "notes": notes.get((event.source_id, event.event_id), ""),
        }
        for event in events
    ]

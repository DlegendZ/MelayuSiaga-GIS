"""Run the accepted local inputs and save an explorable QGIS project."""

import argparse
import gc
import json
import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

try:
    from ._common import ROOT, write_json
except ImportError:
    from _common import ROOT, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT / "data/processed/inputs.gpkg")
    parser.add_argument("--events", type=Path, default=ROOT / "data/processed/events_all.csv")
    parser.add_argument("--sources", type=Path, default=ROOT / "data/clean/sources.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/demo_results.gpkg")
    parser.add_argument(
        "--project", type=Path, default=ROOT / "data/processed/MelayuSiaga_demo.qgz"
    )
    parser.add_argument(
        "--open", action="store_true", help="Open the saved project in desktop QGIS"
    )
    args = parser.parse_args(argv)
    for name in ("inputs", "events", "sources"):
        if not getattr(args, name).is_file():
            parser.error(f"Required local input missing: {getattr(args, name)}")
    for path in (args.output, args.project, args.output.with_suffix(".demo.json")):
        if path.exists():
            parser.error(f"Output exists: {path}; choose a new --output and --project")

    # Preparation is headless; only the requested desktop child uses Windows Qt.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from qgis.core import (
        Qgis,
        QgsApplication,
        QgsProcessingContext,
        QgsProcessingFeedback,
        QgsProject,
        QgsReferencedRectangle,
    )

    app = QgsApplication([], False)
    app.initQgis()
    sys.path.insert(0, str(Path(QgsApplication.pkgDataPath()) / "python/plugins"))
    import processing
    from processing.core.Processing import Processing
    from processing.gui.Postprocessing import handleAlgorithmResults

    from km_flood_priority.provider import KMFloodProvider

    Processing.initialize()
    provider = KMFloodProvider()
    if not QgsApplication.processingRegistry().addProvider(provider):
        raise ValueError("KM Flood Priority provider could not be registered")
    project = QgsProject.instance()
    context = QgsProcessingContext()
    context.setProject(project)
    feedback = QgsProcessingFeedback()
    parameters = {
        "RW_LAYER": f"{args.inputs.resolve()}|layername=rw",
        "RW_FIELD": "wadmrw",
        "ROADS": f"{args.inputs.resolve()}|layername=roads",
        "SAFE_POINTS": f"{args.inputs.resolve()}|layername=safe_points",
        "KELURAHAN_BOUNDARY": f"{args.inputs.resolve()}|layername=kelurahan_boundary",
        "EVENTS_CSV": str(args.events.resolve()),
        "SOURCES_CSV": str(args.sources.resolve()),
        "OUTPUT_GPKG": str(args.output.resolve()),
        "KELURAHAN": "KAMPUNG MELAYU",
        "KECAMATAN": "JATINEGARA",
    }
    try:
        algorithm = QgsApplication.processingRegistry().algorithmById("kmflood:run_pipeline")
        results = processing.run(algorithm, parameters, context=context, feedback=feedback)
        if not handleAlgorithmResults(algorithm, context, feedback, parameters):
            raise ValueError("Could not load all pipeline result layers")
        layers = {layer.name(): layer for layer in project.mapLayers().values()}
        priority = layers["rw_priority"]
        if priority.renderer().type() != "categorizedSymbol":
            raise ValueError("Priority default style was not restored")
        project.setTitle("MelayuSiaga GIS | Recorded 2025 verification priority | Access UNKNOWN")
        project.setCrs(priority.crs())
        extent = layers["kelurahan_boundary"].extent()
        extent.scale(1.15)
        project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(extent, priority.crs()))
        root = project.layerTreeRoot()
        tables = root.addGroup("Tables and provenance")
        for name, layer in layers.items():
            node = root.findLayer(layer.id())
            if not layer.isSpatial():
                tables.addChildNode(node.clone())
                root.removeChildNode(node)
            else:
                node.setExpanded(name == "rw_priority")
                # Candidates remain available for inspection without covering the map.
                node.setItemVisibilityChecked(name != "safe_points")
        tables.setExpanded(False)
        root.setHasCustomLayerOrder(True)
        root.setCustomLayerOrder(
            [
                layers[name]
                for name in (
                    "safe_points",
                    "access_routes",
                    "roads",
                    "rw_priority",
                    "kelurahan_boundary",
                )
            ]
        )
        args.project.parent.mkdir(parents=True, exist_ok=True)
        if not project.write(str(args.project.resolve())):
            raise ValueError("Could not save the demo QGIS project")
        report = {
            "project": str(args.project.resolve()),
            "output": str(args.output.resolve()),
            "qgis_version": Qgis.QGIS_VERSION,
            "pipeline": results,
            "renderers": {
                name: layer.renderer().type() for name, layer in layers.items() if layer.isSpatial()
            },
            "feedback": feedback.textLog(),
        }
        write_json(args.output.with_suffix(".demo.json"), report)
        print(json.dumps({key: report[key] for key in ("project", "output", "renderers")}))
        if args.open:
            executable = (
                Path(QgsApplication.prefixPath()).parents[1] / "bin/qgis-ltr-bin.exe"
                if sys.platform == "win32"
                else Path(shutil.which("qgis") or "")
            )
            if not executable.is_file():
                raise ValueError(
                    "Desktop QGIS executable unavailable; open the saved .qgz manually"
                )
            desktop_environment = {**os.environ}
            desktop_environment["QT_QPA_PLATFORM"] = "windows" if sys.platform == "win32" else "xcb"
            # The GUI intentionally outlives this preparation command.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                subprocess.Popen(
                    [str(executable), "--project", str(args.project.resolve())],
                    env=desktop_environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
            print("Opened desktop QGIS with the saved demo project")
    finally:
        project.clear()
        del context
        gc.collect()
        QgsApplication.processingRegistry().removeProvider(provider)
        app.exitQgis()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"prepare_demo: {error}")

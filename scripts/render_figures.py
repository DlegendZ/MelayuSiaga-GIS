"""Render real-data locator, priority map and method flow using headless QGIS."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

try:
    from ._common import ROOT
    from .build_inputs import initialize_qgis, load_metric
except ImportError:
    from _common import ROOT
    from build_inputs import initialize_qgis, load_metric


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "data/processed/results.gpkg")
    parser.add_argument("--locator", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/figures")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args(argv)
    locator_paths = sorted((ROOT / "data/raw/admin").glob("jakarta_timur_kelurahan_*.geojson"))
    locator = args.locator or (locator_paths[-1] if locator_paths else None)
    if locator is None or not args.results.is_file():
        parser.error("Real result package and official Jakarta Timur locator polygons are required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    application = initialize_qgis()
    from qgis.core import (
        Qgis,
        QgsCategorizedSymbolRenderer,
        QgsFeature,
        QgsFillSymbol,
        QgsGeometry,
        QgsLayoutExporter,
        QgsLayoutItemLabel,
        QgsLayoutItemLegend,
        QgsLayoutItemMap,
        QgsLayoutItemScaleBar,
        QgsLayoutPoint,
        QgsLayoutSize,
        QgsLegendStyle,
        QgsMarkerSymbol,
        QgsPalLayerSettings,
        QgsPrintLayout,
        QgsProject,
        QgsRendererCategory,
        QgsTextFormat,
        QgsVectorLayer,
        QgsVectorLayerSimpleLabeling,
    )
    from qgis.PyQt.QtGui import QColor, QFont

    project = QgsProject.instance()
    metadata = QgsVectorLayer(f"{args.results}|layername=run_info", "run_info", "ogr")
    if not metadata.isValid() or metadata.featureCount() != 1:
        raise ValueError("Result run metadata is missing")
    run = next(metadata.getFeatures())
    years = json.loads(run["years_covered"])
    settings = json.loads(run["parameters_json"])
    year_text = ", ".join(map(str, years))
    events = QgsVectorLayer(f"{args.results}|layername=events", "events", "ogr")
    source_records = {
        (feature["source_id"], feature["event_id"]) for feature in events.getFeatures()
    }
    source_ids = sorted({source for source, _ in source_records})

    def label(layout, text, x, y, width, height, size=9, bold=False):
        item = QgsLayoutItemLabel(layout)
        item.setText(text)
        font = QFont("DejaVu Sans")
        font.setBold(bold)
        format = QgsTextFormat()
        format.setFont(font)
        format.setSize(size)
        format.setColor(QColor("#202020"))
        item.setTextFormat(format)
        layout.addLayoutItem(item)
        item.attemptMove(QgsLayoutPoint(x, y))
        item.attemptResize(QgsLayoutSize(width, height))
        return item

    def map_layout(title, subtitle, layers, extent, filename, *, locator_map=False):
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.pageCollection().pages()[0].setPageSize(
            QgsLayoutSize(220, 165 if locator_map else 180)
        )
        label(layout, title, 7, 3, 205, 9, 14, True)
        label(layout, subtitle, 7, 12, 205, 6, 8)
        item = QgsLayoutItemMap(layout)
        layout.addLayoutItem(item)
        item.attemptMove(QgsLayoutPoint(8, 23))
        item.attemptResize(QgsLayoutSize(139, 111))
        item.setLayers(layers)
        item.setKeepLayerSet(True)
        item.setCrs(layers[0].crs())
        extent.scale(1.18)
        item.zoomToExtent(extent)
        item.setFrameEnabled(True)
        label(layout, "N\n↑", 135, 26, 10, 15, 14, True)
        scale = QgsLayoutItemScaleBar(layout)
        scale.setStyle("Single Box")
        scale.setLinkedMap(item)
        scale.setUnits(Qgis.DistanceUnit.Meters)
        scale.setUnitsPerSegment(5000 if locator_map else 250)
        scale.setNumberOfSegments(2)
        scale.setNumberOfSegmentsLeft(0)
        scale.setUnitLabel("m")
        scale_format = QgsTextFormat()
        scale_format.setSize(7.5)
        scale.setTextFormat(scale_format)
        layout.addLayoutItem(scale)
        scale.attemptMove(QgsLayoutPoint(10, 136))
        legend = QgsLayoutItemLegend(layout)
        legend.setTitle("Locator" if locator_map else "Verification priority")
        legend.setLinkedMap(item)
        legend.setAutoUpdateModel(False)
        legend.setWrapString("|")
        for style in (
            QgsLegendStyle.Style.Title,
            QgsLegendStyle.Style.Group,
            QgsLegendStyle.Style.Subgroup,
            QgsLegendStyle.Style.SymbolLabel,
        ):
            format = QgsTextFormat()
            format.setFont(QFont("DejaVu Sans"))
            format.setSize(10 if style == QgsLegendStyle.Style.Title else 8)
            legend.rstyle(style).setTextFormat(format)
        root = legend.model().rootGroup()
        root.clear()
        for layer in layers:
            if layer.name() not in {"Road context", "Kelurahan boundary"}:
                root.addLayer(legend_priority if layer is priority else layer)
        layout.addLayoutItem(legend)
        legend.attemptMove(QgsLayoutPoint(152, 25))
        legend.attemptResize(QgsLayoutSize(61, 70))
        if locator_map:
            label(
                layout,
                f"Kampung Melayu\nJatinegara, Jakarta Timur\n{priority.featureCount()} RW; "
                f"{area_ha:.2f} ha\n\nIndicative boundaries\nEPSG:32748",
                152,
                100,
                62,
                35,
                9,
            )
        else:
            label(
                layout,
                f"Source years: {year_text}\nHIGH: {counts['HIGH']}; MEDIUM: {counts['MEDIUM']}\n"
                f"VERIFY: {counts['VERIFY']}; NO_RECORD: {counts['NO_RECORD']}\n\n"
                f"Access: {access_description}\nDashed outline: field check\n"
                "Hollow points: unverified",
                152,
                104,
                62,
                38,
                8,
            )
        label(
            layout,
            "Source: DKI indicative kelurahan boundaries, layer 85; "
            "Jakarta Timur locator snapshot 2026-10-13."
            if locator_map
            else f"Sources: DKI indicative administrative boundaries; {', '.join(source_ids)}; "
            "© OpenStreetMap contributors / ODbL.",
            7,
            148,
            207,
            6,
            6.5,
        )
        if not locator_map:
            label(
                layout,
                "Jl. Kebon Pala II: RT 12–13 / RW 04; RT 10–11 / RW 05. "
                "Both RW share 25 source rows; their episode counts must not be added.",
                7,
                163,
                207,
                6,
                6.5,
            )
            label(
                layout,
                "RW polygons are reporting units; these records do not establish "
                "inundation of entire RW. Context and robustness: F2_caption.md.",
                7,
                170,
                207,
                6,
                6.5,
            )
        label(
            layout,
            "Study area context only. Locator point is derived from the boundary; "
            "administrative polygons do not establish flood extent."
            if locator_map
            else "Recorded-event verification priority; no hazard/safety certification. "
            "Source review provenance is retained in events.notes.",
            7,
            155,
            207,
            6,
            6.5,
        )
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = args.dpi
        path = args.output_dir / filename
        result = QgsLayoutExporter(layout).exportToImage(str(path), settings)
        if result != QgsLayoutExporter.ExportResult.Success:
            raise ValueError(f"Could not render {path}: {result}")
        print(f"Rendered {path}")

    def result_layer(name, title, allow_empty=False):
        layer = QgsVectorLayer(f"{args.results}|layername={name}", title, "ogr")
        if not layer.isValid() or not allow_empty and layer.featureCount() == 0:
            raise ValueError(f"Real result layer missing/empty: {name}")
        project.addMapLayer(layer, False)
        return layer

    priority = result_layer("rw_priority", "Recorded RW priority")
    safe = result_layer("safe_points", "Target evidence", allow_empty=True)
    # Keep the package's full target labels; this figure focuses on RW evidence.
    safe.setLabelsEnabled(False)
    roads = result_layer("roads", "Road context")
    boundary = result_layer("kelurahan_boundary", "Kelurahan boundary")
    counts = Counter(feature["priority_class"] for feature in priority.getFeatures())
    legend_priority = priority.clone()
    categories = []
    for category in priority.renderer().categories():
        symbol = category.symbol().clone()
        for index in reversed(range(symbol.symbolLayerCount())):
            if symbol.symbolLayer(index).layerType() == "GeometryGenerator":
                symbol.deleteSymbolLayer(index)
        text = {
            "VERIFY": "Needs verification|weak evidence",
            "NO_RECORD": "No recorded event|(≠ safe)",
        }
        categories.append(
            QgsRendererCategory(
                category.value(), symbol, text.get(category.value(), category.label())
            )
        )
    legend_priority.setRenderer(QgsCategorizedSymbolRenderer("priority_class", categories))
    project.addMapLayer(legend_priority, False)
    if {feature["kelurahan"] for feature in priority.getFeatures()} != {"KAMPUNG MELAYU"}:
        raise ValueError("Product figures require real Kampung Melayu results; no synthetic places")
    area_ha = sum(feature.geometry().area() for feature in boundary.getFeatures()) / 10000
    access = QgsVectorLayer(f"{args.results}|layername=access_by_rw", "access", "ogr")
    statuses = {feature["access_status"] for feature in access.getFeatures()}
    access_description = (
        "UNKNOWN for all RW" if statuses == {"UNKNOWN"} else ", ".join(sorted(statuses))
    )
    routes = result_layer("access_routes", "Route evidence", allow_empty=True)
    map_layers = (
        [safe, routes, boundary, priority, roads]
        if routes.featureCount()
        else [safe, boundary, priority, roads]
    )
    if not isinstance(priority.renderer(), QgsCategorizedSymbolRenderer):
        raise ValueError("Result default priority style is missing")
    subtitle = (
        f"Years: {year_text} • {len(source_records)} source rows / "
        f"{events.featureCount()} RW rows • "
        f"episode gap {settings['EPISODE_GAP_DAYS']} days; "
        f"recurrence {settings['REC_HIGH']}/{settings['REC_MED']}; "
        f"depth {settings['DEPTH_HIGH_CM']} cm"
    )
    map_layout(
        "Recorded-event verification priority — Kampung Melayu",
        subtitle,
        map_layers,
        boundary.extent(),
        "F2_priority_map.png",
    )
    city = load_metric(locator, "Jakarta Timur kelurahan", repair=True)
    city.setName(f"Jakarta Timur ({city.featureCount()} kelurahan)")
    city.renderer().setSymbol(
        QgsFillSymbol.createSimple(
            {"color": "#eeeeee", "outline_color": "#bdbdbd", "outline_width": "0.15"}
        )
    )
    highlight = boundary.clone()
    highlight.setName("Kampung Melayu boundary")
    highlight.renderer().setSymbol(
        QgsFillSymbol.createSimple(
            {"color": "#d7191c", "outline_color": "#d7191c", "outline_width": "0.35"}
        )
    )
    point = QgsVectorLayer("Point?crs=EPSG:32748&field=name:string", "Study area locator", "memory")
    feature = QgsFeature(point.fields())
    feature.setAttributes(["Kampung Melayu"])
    feature.setGeometry(QgsGeometry(next(boundary.getFeatures()).geometry()).pointOnSurface())
    point.dataProvider().addFeatures([feature])
    point.updateExtents()
    point.renderer().setSymbol(
        QgsMarkerSymbol.createSimple(
            {"name": "circle", "color": "#d7191c", "outline_color": "#ffffff", "size": "3"}
        )
    )
    labeling = QgsPalLayerSettings()
    labeling.fieldName = "name"
    text_format = QgsTextFormat()
    text_format.setSize(9)
    labeling.setFormat(text_format)
    point.setLabeling(QgsVectorLayerSimpleLabeling(labeling))
    point.setLabelsEnabled(True)
    project.addMapLayers([city, highlight, point], False)
    map_layout(
        "Study area locator — Jakarta Timur → Kampung Melayu",
        "Official indicative kelurahan boundaries; locator point is derived from the study polygon",
        [point, highlight, city],
        city.extent(),
        "F1_locator.png",
        locator_map=True,
    )
    flow = """<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="340"
viewBox="0 0 1100 340">
<rect width="1100" height="340" fill="white"/>
<g font-family="DejaVu Sans,sans-serif" text-anchor="middle" fill="#222">
<text x="550" y="30" font-size="22" font-weight="bold">
Recorded events → verification priority</text>
<g fill="#eef4fa" stroke="#527795">
<rect x="20" y="60" width="210" height="80" rx="8"/>
<rect x="280" y="60" width="220" height="80" rx="8"/>
<rect x="560" y="60" width="220" height="80" rx="8"/>
<rect x="840" y="60" width="240" height="80" rx="8"/></g>
<g font-size="17"><text x="125" y="91">Source event records</text>
<text x="125" y="119">Accepted source review</text>
<text x="390" y="91">Validate + normalize</text>
<text x="390" y="119">Explode RW; retain NULL</text>
<text x="670" y="91">Distinct episodes</text><text x="670" y="119">Keep depth separate</text>
<text x="960" y="91">RW priority + reasons</text>
<text x="960" y="119">Styled GeoPackage</text></g>
<g stroke="#555" stroke-width="2" fill="none">
<path d="M230 100 H275"/><path d="M500 100 H555"/><path d="M780 100 H835"/>
<path d="M500 235 H810 V165 H960 V145"/></g>
<g fill="#555"><path d="M275 95 L285 100 L275 105 Z"/>
<path d="M550 95 L560 100 L550 105 Z"/>
<path d="M830 95 L840 100 L830 105 Z"/>
<path d="M955 150 L960 140 L965 150 Z"/></g>
<rect x="280" y="190" width="220" height="85" rx="8" fill="#fff4d5" stroke="#ae914a"/>
<text x="390" y="220" font-size="17">Metric OSM road graph</text>
<text x="390" y="247" font-size="17">Verified-only access</text>
<text x="770" y="227" font-size="16">Missing target/closure evidence → UNKNOWN</text>
<text x="770" y="254" font-size="16">Scenario flags do not change classes</text>
<text x="550" y="315" font-size="15">No recorded event (≠ safe). YEAR_COVERAGE.
All spatial processing: EPSG:32748.</text>
</g></svg>"""
    flow = flow.replace("YEAR_COVERAGE", f"Accepted event years: {year_text}")
    (args.output_dir / "F3_method_flow.svg").write_text(flow, encoding="utf-8")
    from qgis.PyQt.QtGui import QImage, QPainter
    from qgis.PyQt.QtSvg import QSvgRenderer

    image = QImage(1100, 340, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    renderer = QSvgRenderer(str(args.output_dir / "F3_method_flow.svg"))
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    if not image.save(str(args.output_dir / "F3_method_flow.png")):
        raise ValueError("Could not render method flow PNG")
    print("Rendered F3_method_flow.svg; human Windows UI screenshots remain pending")
    # Keep QGIS-owned objects alive until process shutdown after rendering.
    _ = application
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(f"render_figures: {error}")

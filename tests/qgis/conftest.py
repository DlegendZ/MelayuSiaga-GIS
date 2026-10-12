"""Headless QGIS fixtures. All locations and source records are synthetic TESTVILLE."""

import csv
import sys
from pathlib import Path

import pytest

pytest.importorskip("qgis.core")
from qgis.core import QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsVectorLayer
from qgis.PyQt.QtCore import QMetaType
from qgis.testing import start_app

from km_flood_priority.core.schema import CLOSURE_COLUMNS, EVENT_COLUMNS, SOURCE_COLUMNS


@pytest.fixture(autouse=True)
def qgis_runtime():
    app = start_app()
    sys.path.insert(0, str(Path(QgsApplication.pkgDataPath()) / "python/plugins"))
    from processing.core.Processing import Processing

    Processing.initialize()
    from km_flood_priority.provider import KMFloodProvider

    provider = KMFloodProvider()
    assert QgsApplication.processingRegistry().addProvider(provider)
    yield app
    current = QgsApplication.processingRegistry().providerById("kmflood")
    if current is not None:
        QgsApplication.processingRegistry().removeProvider(current)


def csv_file(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


def memory_layer(uri, name, fields, features):
    layer = QgsVectorLayer(uri, name, "memory")
    layer.dataProvider().addAttributes([QgsField(key, value) for key, value in fields])
    layer.updateFields()
    for attributes, wkt in features:
        feature = QgsFeature(layer.fields())
        feature.setAttributes(attributes)
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        assert layer.dataProvider().addFeatures([feature])[0]
    layer.updateExtents()
    return layer


@pytest.fixture
def synthetic_inputs(tmp_path):
    x, y = 500000, 9300000
    rw_features = []
    for number, offset in enumerate([0, 100, 200, 250], start=1):
        left, right, bottom, top = x + offset - 10, x + offset + 10, y - 10, y + 10
        polygon = (
            f"POLYGON(({left} {bottom},{right} {bottom},{right} {top},"
            f"{left} {top},{left} {bottom}))"
        )
        rw_features.append(([f"{number:03}"], polygon))
    rw = memory_layer(
        "Polygon?crs=EPSG:32748", "TESTVILLE RW", [("wadmrw", QMetaType.Type.QString)], rw_features
    )
    roads = memory_layer(
        "LineString?crs=EPSG:32748",
        "TESTVILLE roads",
        [(name, QMetaType.Type.QString) for name in ("osm_id", "highway", "name")],
        [
            (["TEST-LEFT", "residential", "TESTVILLE west"], f"LINESTRING({x} {y},{x + 100} {y})"),
            (
                ["TEST-BRIDGE", "residential", "TESTVILLE bridge"],
                f"LINESTRING({x + 100} {y},{x + 200} {y})",
            ),
            (
                ["TEST-RIGHT", "residential", "TESTVILLE east"],
                f"LINESTRING({x + 200} {y},{x + 250} {y},{x + 300} {y})",
            ),
        ],
    )
    safe = memory_layer(
        "Point?crs=EPSG:32748",
        "TESTVILLE candidate",
        [
            (name, QMetaType.Type.QString)
            for name in (
                "sp_id",
                "name",
                "sp_type",
                "capacity",
                "lon",
                "lat",
                "verified",
                "source_id",
                "source_ref",
                "notes",
            )
        ],
        [
            (
                [
                    "TEST-SP",
                    "TESTVILLE refuge",
                    "TEST",
                    None,
                    None,
                    None,
                    "Y",
                    "SYNTHETIC",
                    "TEST source",
                    "Synthetic only",
                ],
                f"POINT({x + 300} {y})",
            )
        ],
    )
    boundary = memory_layer(
        "Polygon?crs=EPSG:32748",
        "TESTVILLE boundary",
        [],
        [
            (
                [],
                f"POLYGON(({x - 20} {y - 20},{x + 320} {y - 20},{x + 320} {y + 20},"
                f"{x - 20} {y + 20},{x - 20} {y - 20}))",
            )
        ],
    )
    events = []
    for index, (number, day, depth) in enumerate(
        [
            (1, "2025-03-04", "80"),
            (1, "2025-07-07", "80"),
            (1, "2025-08-04", "80"),
            (2, "2025-03-04", "20"),
            (2, "2025-07-07", "20"),
            (3, "2025-03-04", "20"),
            (None, "2025-03-04", "30"),
            (1, "2025-03-04", ""),
        ]
    ):
        row = dict.fromkeys(EVENT_COLUMNS, "")
        row.update(
            event_id=f"TEST-{index}",
            source_id="SYNTHETIC" if index < 7 else "SYNTHETIC2",
            source_ref=f"TEST row {index}",
            event_date=day,
            kota="TEST CITY",
            kelurahan="TESTVILLE",
            kecamatan="TEST DISTRICT",
            rw_raw=str(number or ""),
            depth_raw=depth,
            location_confidence="RW" if number else "UNKNOWN",
            verified="Y",
            notes="Synthetic only; no real place or finding",
        )
        events.append(row)
    sources = [
        {
            **dict.fromkeys(SOURCE_COLUMNS, ""),
            "source_id": source,
            "title": "TESTVILLE synthetic source",
            "publisher": "TEST ONLY",
            "url": "https://example.invalid/test",
            "retrieved_on": "2025-01-01",
            "license_terms": "Synthetic fixture",
            "format": "CSV",
            "coverage_years": "2025",
        }
        for source in ("SYNTHETIC", "SYNTHETIC2")
    ]
    closures = [
        {
            "closure_id": "TEST-CLOSE",
            "event_date": "2025-03-04",
            "road_ref_type": "OSM_ID",
            "road_ref": "TEST-BRIDGE",
            "verified": "Y",
            "source_id": "SYNTHETIC",
            "source_ref": "TEST source",
            "notes": "Synthetic only",
        }
    ]
    return {
        "RW_LAYER": rw,
        "RW_FIELD": "wadmrw",
        "ROADS": roads,
        "SAFE_POINTS": safe,
        "KELURAHAN_BOUNDARY": boundary,
        "KELURAHAN": "TESTVILLE",
        "KECAMATAN": "TEST DISTRICT",
        "EVENTS_CSV": csv_file(tmp_path / "events.csv", EVENT_COLUMNS, events),
        "SOURCES_CSV": csv_file(tmp_path / "sources.csv", SOURCE_COLUMNS, sources),
        "CLOSURES_CSV": csv_file(tmp_path / "closures.csv", CLOSURE_COLUMNS, closures),
    }

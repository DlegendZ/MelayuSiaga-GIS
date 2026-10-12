"""Integration acceptance of the real Processing algorithms on synthetic inputs."""

import sqlite3
from pathlib import Path

import pytest
from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback, QgsVectorLayer
from qgis.PyQt.QtCore import QMetaType

EXPECTED_LAYERS = {
    "rw_priority",
    "priority_table",
    "events",
    "validation_issues",
    "access_by_rw",
    "access_routes",
    "safe_points",
    "roads",
    "kelurahan_boundary",
    "sources",
    "run_info",
}


def run_pipeline(inputs, path):
    import processing

    context = QgsProcessingContext()
    result = processing.run(
        "kmflood:run_pipeline",
        {**inputs, "OUTPUT_GPKG": str(path)},
        context=context,
        feedback=QgsProcessingFeedback(),
    )
    assert Path(result["OUTPUT_GPKG"]).is_file()
    return result


def test_all_five_algorithm_ids_are_registered():
    provider = QgsApplication.processingRegistry().providerById("kmflood")
    assert {algorithm.name() for algorithm in provider.algorithms()} == {
        "import_validate",
        "test_access",
        "compute_priority",
        "export_package",
        "run_pipeline",
    }


def test_pipeline_package_schema_styles_and_claims(synthetic_inputs, tmp_path):
    path = tmp_path / "testville.gpkg"
    run_pipeline(synthetic_inputs, path)
    with sqlite3.connect(path) as connection:
        layers = {row[0] for row in connection.execute("SELECT table_name FROM gpkg_contents")}
        assert EXPECTED_LAYERS <= layers
        assert connection.execute("SELECT count(*) FROM events").fetchone()[0] == 8
        assert connection.execute("SELECT count(*) FROM priority_table").fetchone()[0] == 5
        assert connection.execute("SELECT count(*) FROM access_by_rw").fetchone()[0] == 12
        classes = dict(connection.execute("SELECT rw_no,priority_class FROM rw_priority"))
        assert classes == {1: "HIGH", 2: "MEDIUM", 3: "VERIFY", 4: "NO_RECORD"}
        assert (
            connection.execute(
                "SELECT count(*) FROM events WHERE duplicate_of IS NOT NULL"
            ).fetchone()[0]
            == 1
        )
        styles = {
            row[0]
            for row in connection.execute(
                "SELECT f_table_name FROM layer_styles WHERE useAsDefault=1"
            )
        }
        assert {
            "rw_priority",
            "access_routes",
            "safe_points",
            "roads",
            "kelurahan_boundary",
        } <= styles
        assert (
            connection.execute("SELECT class_reason FROM rw_priority WHERE rw_no=4")
            .fetchone()[0]
            .startswith("No recorded event")
        )
    layer = QgsVectorLayer(f"{path}|layername=events", "events", "ogr")
    assert layer.fields().field("event_date").type() == QMetaType.Type.QDate
    assert layer.fields().field("rw_no").type() in {QMetaType.Type.Int, QMetaType.Type.LongLong}
    priority = QgsVectorLayer(f"{path}|layername=rw_priority", "priority", "ogr")
    assert priority.crs().authid() == "EPSG:32748"
    assert priority.renderer().type() == "categorizedSymbol"
    assert all(feature.geometry().isGeosValid() for feature in priority.getFeatures())


def test_missing_evidence_produces_unknown(synthetic_inputs, tmp_path):
    inputs = {**synthetic_inputs}
    inputs.pop("SAFE_POINTS")
    inputs.pop("CLOSURES_CSV")
    path = tmp_path / "unknown.gpkg"
    run_pipeline(inputs, path)
    with sqlite3.connect(path) as connection:
        assert {
            row[0] for row in connection.execute("SELECT DISTINCT access_status FROM access_by_rw")
        } == {"UNKNOWN"}
        assert connection.execute("SELECT count(*) FROM access_routes").fetchone()[0] == 0
        assert {
            row[0]
            for row in connection.execute("SELECT DISTINCT needs_field_check FROM rw_priority")
        } == {"Y"}


def test_pipeline_is_deterministic_except_run_identity(synthetic_inputs, tmp_path):
    paths = [tmp_path / "first.gpkg", tmp_path / "second.gpkg"]
    for path in paths:
        run_pipeline(synthetic_inputs, path)
    with sqlite3.connect(paths[0]) as first, sqlite3.connect(paths[1]) as second:
        for table in ("events", "validation_issues", "priority_table", "access_by_rw"):
            fields = [
                row[1]
                for row in first.execute(f'PRAGMA table_info("{table}")')
                if row[1] not in {"fid", "run_id"}
            ]
            columns = ",".join(f'"{field}"' for field in fields)
            query = f'SELECT {columns} FROM "{table}" ORDER BY fid'
            assert first.execute(query).fetchall() == second.execute(query).fetchall()


def test_existing_package_requires_explicit_overwrite(synthetic_inputs, tmp_path):
    from qgis.core import QgsProcessingException

    path = tmp_path / "protected.gpkg"
    run_pipeline(synthetic_inputs, path)
    original = path.read_bytes()
    with pytest.raises(QgsProcessingException, match="exist"):
        run_pipeline(synthetic_inputs, path)
    assert path.read_bytes() == original

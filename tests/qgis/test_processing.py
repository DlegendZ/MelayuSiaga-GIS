"""Integration acceptance of the real Processing algorithms on synthetic inputs."""

import sqlite3
from pathlib import Path

import pytest
from qgis.core import (
    QgsApplication,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
    QgsVectorLayer,
)
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


@pytest.mark.parametrize("execution_mode", ["context_transfer", "gui_worker"])
def test_gui_completion_loads_final_package_with_default_priority_style(
    synthetic_inputs, tmp_path, execution_mode
):
    import gc

    import processing
    from processing.gui.Postprocessing import handleAlgorithmResults
    from qgis.core import QgsProcessingAlgRunnerTask
    from qgis.PyQt.QtCore import QEventLoop, QTimer

    project = QgsProject()
    feedback = QgsProcessingFeedback()
    parameters = {**synthetic_inputs, "OUTPUT_GPKG": str(tmp_path / "gui-final.gpkg")}
    algorithm = QgsApplication.processingRegistry().algorithmById("kmflood:run_pipeline")

    def execute_with_temporary_context():
        execution_context = QgsProcessingContext()
        execution_context.setProject(project)
        if execution_mode == "gui_worker":
            # AlgorithmDialog uses this background task, whose processAlgorithm
            # receives a temporary SIP context wrapper on the worker thread.
            loop = QEventLoop()
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(loop.quit)
            outcome = {}

            def finished(successful, results):
                outcome["success"] = successful
                loop.quit()

            task = QgsProcessingAlgRunnerTask(algorithm, parameters, execution_context, feedback)
            task.executed.connect(finished)
            QgsApplication.taskManager().addTask(task)
            timer.start(20000)
            loop.exec()
            timer.stop()
            assert outcome.get("success"), feedback.textLog()
        else:
            processing.run(algorithm, parameters, context=execution_context, feedback=feedback)
        completion_context = QgsProcessingContext()
        completion_context.setProject(project)
        completion_context.takeResultsFrom(execution_context)
        # Keep only the C++ completion results, not the execution wrapper or its
        # arbitrary Python attributes. Real GUI worker contexts are temporary.
        return completion_context

    context = execute_with_temporary_context()
    # No test reference to callbacks or the original context may keep them alive.
    gc.collect()
    try:
        assert handleAlgorithmResults(algorithm, context, feedback, parameters)
        layers = {layer.name(): layer for layer in project.mapLayers().values()}
        assert set(layers) == EXPECTED_LAYERS
        priority = layers["rw_priority"]
        assert priority.source() == f"{parameters['OUTPUT_GPKG']}|layername=rw_priority"
        assert priority.renderer().type() == "categorizedSymbol"
        assert {category.value() for category in priority.renderer().categories()} == {
            "HIGH",
            "MEDIUM",
            "VERIFY",
            "NO_RECORD",
        }
        assert priority.labelsEnabled()
        for name in ("safe_points", "access_routes"):
            assert layers[name].renderer().type() == "categorizedSymbol"
        # These two defaults intentionally use a single symbol. Check their
        # appearance so a random Processing symbol cannot pass as a valid style.
        roads_symbol = layers["roads"].renderer().symbol()
        assert roads_symbol.color().name() == "#bdbdbd"
        assert roads_symbol.width() == pytest.approx(0.15)
        boundary_symbol = layers["kelurahan_boundary"].renderer().symbol().symbolLayer(0)
        assert boundary_symbol.strokeColor().name() == "#252525"
        assert boundary_symbol.strokeWidth() == pytest.approx(0.8)
        log = feedback.textLog()
        for name in ("rw_priority", "access_routes", "safe_points", "roads", "kelurahan_boundary"):
            assert f"postProcessLayer({name})" in log
            assert f"restored {name} style" in log
        assert "Could not load embedded" not in log
    finally:
        project.removeAllMapLayers()


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

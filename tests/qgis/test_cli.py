"""ZIP installation and qgis_process run in an isolated container-side profile."""

import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

from qgis.core import QgsProject, QgsVectorFileWriter

from scripts.package_plugin import build_archive


def test_zip_install_and_qgis_process_pipeline(synthetic_inputs, tmp_path):
    package = build_archive(tmp_path / "plugin.zip")
    with tempfile.TemporaryDirectory(prefix="kmflood-cli-") as isolated:
        isolated = Path(isolated)
        plugins, config = isolated / "plugins", isolated / "config"
        plugins.mkdir()
        config.mkdir()
        with zipfile.ZipFile(package) as archive:
            assert all(name.startswith("km_flood_priority/") for name in archive.namelist())
            assert not any(name.endswith((".pyc", ".gpkg")) for name in archive.namelist())
            assert not any("/sample_data/" in name for name in archive.namelist())
            archive.extractall(plugins)
        environment = {
            **os.environ,
            "QGIS_PLUGINPATH": str(plugins),
            "QGIS_CUSTOM_CONFIG_PATH": str(config),
            "XDG_CONFIG_HOME": str(config),
            "QT_QPA_PLATFORM": "offscreen",
        }
        enabled = subprocess.run(
            ["qgis_process", "plugins", "enable", "km_flood_priority"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert enabled.returncode == 0, enabled.stdout + enabled.stderr
        inputs = {key: item for key, item in synthetic_inputs.items() if isinstance(item, str)}
        for key in ("RW_LAYER", "ROADS", "SAFE_POINTS", "KELURAHAN_BOUNDARY"):
            path = isolated / f"{key.lower()}.gpkg"
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            result = QgsVectorFileWriter.writeAsVectorFormatV3(
                synthetic_inputs[key], str(path), QgsProject.instance().transformContext(), options
            )
            assert result[0] == QgsVectorFileWriter.WriterError.NoError
            inputs[key] = str(path)
        output = isolated / "results.gpkg"
        inputs["OUTPUT_GPKG"] = str(output)
        run = subprocess.run(
            ["qgis_process", "run", "kmflood:run_pipeline", "-"],
            input=json.dumps({"inputs": inputs}),
            env=environment,
            capture_output=True,
            text=True,
            timeout=45,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        assert output.is_file()
        payload = json.loads(run.stdout)
        assert payload["results"]["OUTPUT_SUMMARY"]["years_covered"] == [2025]

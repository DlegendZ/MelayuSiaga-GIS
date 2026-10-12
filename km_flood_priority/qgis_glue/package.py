"""Atomic GeoPackage export, with embedded defaults and no silent replacement."""

import gc
import os
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from qgis.core import QgsVectorFileWriter, QgsVectorLayer

from .styles import SPATIAL_STYLES, save_default_style


def write_package(layers, output, context, feedback, *, overwrite=False):
    output = Path(output)
    if output.exists() and not overwrite:
        raise ValueError("Output exists; choose a new filename or explicitly enable OVERWRITE")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}-{uuid.uuid4().hex}.gpkg")
    try:
        for index, (name, layer) in enumerate(layers.items()):
            if feedback.isCanceled():
                raise ValueError("Processing canceled before package completion")
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName, options.layerName, options.fileEncoding = "GPKG", name, "UTF-8"
            options.actionOnExistingFile = (
                QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
                if index == 0
                else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
            )
            result = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, str(temporary), context.transformContext(), options
            )
            if result[0] != QgsVectorFileWriter.WriterError.NoError:
                raise ValueError(f"Writing {name} failed: {result[1]}")
        for name in sorted(SPATIAL_STYLES):
            saved = QgsVectorLayer(f"{temporary}|layername={name}", name, "ogr")
            if not saved.isValid():
                raise ValueError(f"Could not reopen {name} for embedded style")
            save_default_style(saved, name)
            saved = None
        gc.collect()
        # sqlite3's transaction context manager does not close the connection.
        # Close it explicitly and checkpoint WAL data before moving the database.
        with closing(sqlite3.connect(temporary)) as connection:
            styled = {
                row[0]
                for row in connection.execute(
                    "SELECT f_table_name FROM layer_styles WHERE useAsDefault=1"
                )
            }
            if not SPATIAL_STYLES <= styled:
                raise ValueError("Default styles were not embedded for every spatial layer")
            if connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]:
                raise ValueError("GeoPackage has an active WAL writer; output was not replaced")
        # A failed export leaves an existing output untouched.
        os.replace(temporary, output)
        return str(output)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise

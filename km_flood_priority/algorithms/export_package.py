"""FR-4 styled result package with provenance and run metadata."""

import json
import uuid
from datetime import datetime, timezone

from qgis.core import (
    Qgis,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterString,
)

from .. import __version__
from ..qgis_glue.fields import ACCESS_FIELDS, ROUTE_FIELDS, RUN_FIELDS, SAFE_FIELDS, SOURCE_FIELDS
from ..qgis_glue.io import (
    date_value,
    make_layer,
    metric_copy,
    read_sources,
    rows_from_source,
    table_copy,
)
from ..qgis_glue.package import write_package
from .base import KMFloodAlgorithm


class ExportPackageAlgorithm(KMFloodAlgorithm):
    NAME, TITLE = "export_package", "Export styled result GeoPackage"
    GROUP, GROUP_ID = "3. Output", "output"
    HELP = (
        "Combine priority, event and validation tables with access, roads, target evidence and "
        "the kelurahan boundary. Embed default QML for every spatial layer and include sources "
        "and run metadata. Output replacement requires explicit OVERWRITE; failed exports "
        "leave an existing package unchanged."
    )

    def initAlgorithm(self, config=None):
        for key, label, types, optional in (
            ("PRIORITY", "RW verification priority", [QgsProcessing.TypeVectorPolygon], False),
            ("PRIORITY_TABLE", "Priority summary table", [], False),
            ("EVENTS", "Normalized events", [], False),
            ("VALIDATION_ISSUES", "Validation issues", [], False),
            ("ACCESS", "Access by RW and date", [], True),
            ("ROUTES", "Access routes", [QgsProcessing.TypeVectorLine], True),
            ("ROADS", "Road context", [QgsProcessing.TypeVectorLine], False),
            ("SAFE_POINTS", "Safe-point evidence", [QgsProcessing.TypeVectorPoint], True),
            ("KELURAHAN_BOUNDARY", "Kelurahan boundary", [QgsProcessing.TypeVectorPolygon], False),
        ):
            self.addParameter(
                QgsProcessingParameterFeatureSource(key, label, types, optional=optional)
            )
        self.addParameter(
            QgsProcessingParameterFile("SOURCES_CSV", "Source registry CSV", extension="csv")
        )
        self.addParameter(
            QgsProcessingParameterString(
                "RUN_PARAMETERS", "Run parameters JSON", "{}", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "RUN_ID", "Run identifier (blank: priority ID)", "", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean("OVERWRITE", "Replace an existing output package", False)
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                "OUTPUT_GPKG", "Result GeoPackage", "GeoPackage (*.gpkg)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        try:
            sources = read_sources(self.parameterAsFile(parameters, "SOURCES_CSV", context))
            layers = {}
            for key, name in (
                ("PRIORITY", "rw_priority"),
                ("PRIORITY_TABLE", "priority_table"),
                ("EVENTS", "events"),
                ("VALIDATION_ISSUES", "validation_issues"),
                ("ACCESS", "access_by_rw"),
                ("ROUTES", "access_routes"),
            ):
                source = self.parameterAsSource(parameters, key, context)
                if source is None:
                    specification = ACCESS_FIELDS if key == "ACCESS" else ROUTE_FIELDS
                    layers[name] = make_layer(
                        name, "None" if key == "ACCESS" else "LineString", specification
                    )
                elif key in {"PRIORITY", "ROUTES"}:
                    layers[name] = metric_copy(source, name, context)
                else:
                    layers[name] = table_copy(source, name)
            for key, name in (
                ("ROADS", "roads"),
                ("SAFE_POINTS", "safe_points"),
                ("KELURAHAN_BOUNDARY", "kelurahan_boundary"),
            ):
                source = self.parameterAsSource(parameters, key, context)
                layers[name] = (
                    metric_copy(source, name, context)
                    if source is not None
                    else make_layer(name, "Point", SAFE_FIELDS)
                )
            layers["sources"] = make_layer("sources", "None", SOURCE_FIELDS, sources)
            events = rows_from_source(layers["events"])
            years = sorted({date_value(row["event_date"]).year for row in events})
            priority = rows_from_source(layers["priority_table"])
            identifiers = {row["run_id"] for row in priority if row.get("run_id")}
            if len(identifiers) > 1:
                raise ValueError("Priority table contains more than one run_id")
            run_id = self.parameterAsString(parameters, "RUN_ID", context) or next(
                iter(identifiers), str(uuid.uuid4())
            )
            if identifiers and identifiers != {run_id}:
                raise ValueError("RUN_ID does not match the priority outputs")
            settings = json.loads(
                self.parameterAsString(parameters, "RUN_PARAMETERS", context) or "{}"
            )
            if not isinstance(settings, dict):
                raise ValueError("RUN_PARAMETERS must be a JSON object")
            layers["run_info"] = make_layer(
                "run_info",
                "None",
                RUN_FIELDS,
                [
                    {
                        "run_id": run_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "plugin_version": __version__,
                        "qgis_version": Qgis.QGIS_VERSION,
                        "parameters_json": json.dumps(settings, sort_keys=True),
                        "years_covered": json.dumps(years),
                    }
                ],
            )
            output = write_package(
                layers,
                self.parameterAsFileOutput(parameters, "OUTPUT_GPKG", context),
                context,
                feedback,
                overwrite=self.parameterAsBool(parameters, "OVERWRITE", context),
            )
            return {"OUTPUT_GPKG": output}
        except (ValueError, OSError, KeyError) as error:
            raise QgsProcessingException(str(error)) from error

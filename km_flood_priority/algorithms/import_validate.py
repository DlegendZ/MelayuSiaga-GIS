"""FR-1 canonical event import with retained duplicates and validation issues."""

import json
from dataclasses import asdict

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingOutputVariant,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
)

from ..core.normalize import import_events
from ..core.schema import EVENT_REQUIRED
from ..qgis_glue.fields import EVENT_FIELDS, ISSUE_FIELDS
from ..qgis_glue.io import event_records, make_layer, output_layer, read_csv, read_sources, rw_units
from .base import KMFloodAlgorithm


class ImportValidateAlgorithm(KMFloodAlgorithm):
    NAME, TITLE = "import_validate", "Import & validate recorded events"
    GROUP, GROUP_ID = "1. Input", "input"
    HELP = (
        "Read canonical UTF-8 CSVs and a source registry; filter by kelurahan and district, "
        "normalize dates/RWs/depths, explode multi-RW rows and retain cross-source duplicates. "
        "Outputs are normalized events, validation issues and a summary. Schema errors or "
        "zero valid rows fail; individual row errors are retained as issues."
    )

    def initAlgorithm(self, config=None):
        self.add_rw()
        self.add_area()
        for key, label, optional in (
            ("EVENTS_CSV", "Canonical events CSV", False),
            ("EXTRA_EVENTS_CSV", "Additional events CSV", True),
            ("SOURCES_CSV", "Source registry CSV", False),
        ):
            self.addParameter(
                QgsProcessingParameterFile(key, label, extension="csv", optional=optional)
            )
        self.addParameter(
            QgsProcessingParameterString(
                "SOURCE_PRIORITY", "Source priority (comma-separated IDs)", "", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT_EVENTS", "Normalized events", QgsProcessing.TypeVector
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT_ISSUES", "Validation issues", QgsProcessing.TypeVector
            )
        )
        self.addOutput(QgsProcessingOutputVariant("OUTPUT_SUMMARY", "Validation summary"))

    def processAlgorithm(self, parameters, context, feedback):
        try:
            units = rw_units(
                self.parameterAsSource(parameters, "RW_LAYER", context),
                self.parameterAsString(parameters, "RW_FIELD", context),
                context,
            )
            sources = read_sources(self.parameterAsFile(parameters, "SOURCES_CSV", context))
            rows = []
            for key in ("EVENTS_CSV", "EXTRA_EVENTS_CSV"):
                path = self.parameterAsFile(parameters, key, context)
                if path:
                    headers, items = read_csv(path)
                    from ..core.validation import require_columns

                    require_columns(headers, EVENT_REQUIRED)
                    rows.extend(items)
            result = import_events(
                rows,
                columns=EVENT_REQUIRED,
                rw_numbers=set(units),
                source_ids={row["source_id"] for row in sources},
                kelurahan=self.parameterAsString(parameters, "KELURAHAN", context),
                kecamatan=self.parameterAsString(parameters, "KECAMATAN", context),
                source_priority=[
                    item.strip()
                    for item in self.parameterAsString(
                        parameters, "SOURCE_PRIORITY", context
                    ).split(",")
                    if item.strip()
                ],
            )
            events = make_layer("events", "None", EVENT_FIELDS, event_records(result.events, rows))
            issues = make_layer(
                "validation_issues",
                "None",
                ISSUE_FIELDS,
                [asdict(issue) for issue in result.issues],
            )
            feedback.pushInfo(json.dumps(result.summary, sort_keys=True))
            return {
                "OUTPUT_EVENTS": output_layer(
                    self, parameters, "OUTPUT_EVENTS", context, events, feedback
                ),
                "OUTPUT_ISSUES": output_layer(
                    self, parameters, "OUTPUT_ISSUES", context, issues, feedback
                ),
                "OUTPUT_SUMMARY": result.summary,
            }
        except (ValueError, OSError, KeyError) as error:
            raise QgsProcessingException(str(error)) from error

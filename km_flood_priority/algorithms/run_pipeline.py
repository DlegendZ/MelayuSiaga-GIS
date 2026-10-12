"""FR-5 main entry point orchestrating the four child Processing algorithms."""

import json
import time
import uuid

from qgis.core import (
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingMultiStepFeedback,
    QgsProcessingOutputNumber,
    QgsProcessingOutputVariant,
)

from ..qgis_glue.io import events_from_source
from ..qgis_glue.styles import SPATIAL_STYLES, PackageStylePostProcessor
from .base import KMFloodAlgorithm
from .compute_priority import ComputePriorityAlgorithm
from .export_package import ExportPackageAlgorithm
from .import_validate import ImportValidateAlgorithm
from .test_access import TestAccessAlgorithm


class RunPipelineAlgorithm(KMFloodAlgorithm):
    NAME, TITLE = "run_pipeline", "Run full recorded-event verification pipeline"
    GROUP, GROUP_ID = "0. Pipeline", "pipeline"
    HELP = (
        "Run import/validation, verified-evidence access, RW classification and styled "
        "GeoPackage export. Blank EVENT_DATES uses the imported event dates; ALL uses "
        "closure dates. Results include provenance and an unassigned summary. Optional "
        "targets/closures may be omitted; missing evidence yields UNKNOWN. No network calls."
    )

    def initAlgorithm(self, config=None):
        self.child_keys = {}
        skipped = {
            "EVENTS",
            "ACCESS",
            "PRIORITY",
            "PRIORITY_TABLE",
            "VALIDATION_ISSUES",
            "ROUTES",
            "RUN_ID",
            "RUN_PARAMETERS",
        }
        for algorithm_class in (
            ImportValidateAlgorithm,
            TestAccessAlgorithm,
            ComputePriorityAlgorithm,
            ExportPackageAlgorithm,
        ):
            algorithm = algorithm_class()
            algorithm.initAlgorithm()
            keys = []
            for definition in algorithm.parameterDefinitions():
                name = definition.name()
                keys.append(name)
                if (
                    name in skipped
                    or name.startswith("OUTPUT_")
                    and name != "OUTPUT_GPKG"
                    or self.parameterDefinition(name) is not None
                ):
                    continue
                clone = definition.clone()
                if name == "EVENT_DATES":
                    clone.setDescription("ISO dates (blank: imported dates; ALL: closures)")
                self.addParameter(clone)
            self.child_keys[algorithm.name()] = keys
        self.addOutput(QgsProcessingOutputVariant("OUTPUT_SUMMARY", "Import validation summary"))
        self.addOutput(QgsProcessingOutputVariant("OUTPUT_GRAPH_STATS", "Graph statistics"))
        self.addOutput(QgsProcessingOutputNumber("ELAPSED_SECONDS", "Elapsed processing seconds"))

    def processAlgorithm(self, parameters, context, feedback):
        import processing

        started = time.perf_counter()
        run_id = str(uuid.uuid4())
        stages = QgsProcessingMultiStepFeedback(4, feedback)

        def child(name, overrides):
            values = {key: parameters[key] for key in self.child_keys[name] if key in parameters}
            values.update(overrides)
            return processing.run(
                f"kmflood:{name}", values, context=context, feedback=stages, is_child_algorithm=True
            )

        stages.setCurrentStep(0)
        imported = child(
            "import_validate",
            {
                "OUTPUT_EVENTS": QgsProcessing.TEMPORARY_OUTPUT,
                "OUTPUT_ISSUES": QgsProcessing.TEMPORARY_OUTPUT,
            },
        )
        dates = self.parameterAsString(parameters, "EVENT_DATES", context)
        if not dates.strip():
            events = events_from_source(context.getMapLayer(imported["OUTPUT_EVENTS"]))
            dates = ",".join(sorted({event.event_date.isoformat() for event in events}))
        stages.setCurrentStep(1)
        accessed = child(
            "test_access",
            {
                "EVENT_DATES": dates,
                "OUTPUT_ACCESS": QgsProcessing.TEMPORARY_OUTPUT,
                "OUTPUT_ROUTES": QgsProcessing.TEMPORARY_OUTPUT,
            },
        )
        stages.setCurrentStep(2)
        classified = child(
            "compute_priority",
            {
                "EVENTS": imported["OUTPUT_EVENTS"],
                "ACCESS": accessed["OUTPUT_ACCESS"],
                "RUN_ID": run_id,
                "OUTPUT_PRIORITY": QgsProcessing.TEMPORARY_OUTPUT,
                "OUTPUT_PRIORITY_TABLE": QgsProcessing.TEMPORARY_OUTPUT,
            },
        )
        settings = {
            key: item
            for key, item in parameters.items()
            if isinstance(item, (str, int, float, bool)) and not key.startswith("OUTPUT_")
        }
        for key in ("EPISODE_GAP_DAYS", "REC_HIGH", "REC_MED", "DEPTH_HIGH_CM"):
            settings[key] = self.parameterAsInt(parameters, key, context)
        settings["SNAP_TOLERANCE_M"] = self.parameterAsDouble(
            parameters, "SNAP_TOLERANCE_M", context
        )
        settings["USE_UNVERIFIED_SAFE_POINTS"] = self.parameterAsBool(
            parameters, "USE_UNVERIFIED_SAFE_POINTS", context
        )
        settings["EVENT_DATES"] = dates
        stages.setCurrentStep(3)
        exported = child(
            "export_package",
            {
                "PRIORITY": classified["OUTPUT_PRIORITY"],
                "PRIORITY_TABLE": classified["OUTPUT_PRIORITY_TABLE"],
                "EVENTS": imported["OUTPUT_EVENTS"],
                "VALIDATION_ISSUES": imported["OUTPUT_ISSUES"],
                "ACCESS": accessed["OUTPUT_ACCESS"],
                "ROUTES": accessed["OUTPUT_ROUTES"],
                "RUN_ID": run_id,
                "RUN_PARAMETERS": json.dumps(settings, sort_keys=True),
            },
        )
        if context.project() is not None:
            for name in (
                "rw_priority",
                "access_routes",
                "safe_points",
                "roads",
                "kelurahan_boundary",
                "events",
                "validation_issues",
                "access_by_rw",
                "priority_table",
                "sources",
                "run_info",
            ):
                details = QgsProcessingContext.LayerDetails(name, context.project(), "OUTPUT_GPKG")
                if name in SPATIAL_STYLES:
                    processor = PackageStylePostProcessor.create(exported["OUTPUT_GPKG"], name)
                    details.setPostProcessor(processor)
                context.addLayerToLoadOnCompletion(
                    f"{exported['OUTPUT_GPKG']}|layername={name}", details
                )
        return {
            **exported,
            "OUTPUT_SUMMARY": imported["OUTPUT_SUMMARY"],
            "OUTPUT_GRAPH_STATS": accessed["OUTPUT_GRAPH_STATS"],
            "ELAPSED_SECONDS": time.perf_counter() - started,
        }

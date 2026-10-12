"""FR-3 transparent RW classification delegated to the pure Python core."""

import uuid
from dataclasses import asdict

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from ..core.normalize import parse_rw
from ..core.priority import compute_priority
from ..core.schema import PriorityParameters
from ..qgis_glue.fields import PRIORITY_FIELDS
from ..qgis_glue.io import (
    access_from_source,
    events_from_source,
    make_layer,
    output_layer,
    rw_units,
    value,
)
from .base import KMFloodAlgorithm


class ComputePriorityAlgorithm(KMFloodAlgorithm):
    NAME, TITLE = "compute_priority", "Compute verification priority from recorded events"
    HELP = (
        "Aggregate normalized countable records and distinct episodes by RW, keeping maximum "
        "depth and evidence gaps separate. Classify HIGH/MEDIUM/VERIFY/NO_RECORD using the "
        "displayed thresholds and worst event access. Scenario RW lists are comparators only. "
        "Outputs are RW polygons and a table including an unassigned summary row."
    )

    def initAlgorithm(self, config=None):
        self.add_rw()
        self.addParameter(QgsProcessingParameterFeatureSource("EVENTS", "Normalized events"))
        self.addParameter(
            QgsProcessingParameterFeatureSource("ACCESS", "Access by RW and date", optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "SCENARIO_LAYER", "Scenario RW list (comparator)", optional=True
            )
        )
        for key, label, default, minimum in (
            ("EPISODE_GAP_DAYS", "Episode gap (days)", 2, 0),
            ("REC_HIGH", "High recurrence threshold", 3, 1),
            ("REC_MED", "Medium recurrence threshold", 2, 1),
            ("DEPTH_HIGH_CM", "High recorded depth threshold (cm)", 50, 0),
        ):
            self.addParameter(
                QgsProcessingParameterNumber(
                    key, label, QgsProcessingParameterNumber.Integer, default, minValue=minimum
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                "RUN_ID", "Run identifier (blank: new UUID)", "", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT_PRIORITY", "RW verification priority", QgsProcessing.TypeVectorPolygon
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT_PRIORITY_TABLE", "Priority summary table", QgsProcessing.TypeVector
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        try:
            units = rw_units(
                self.parameterAsSource(parameters, "RW_LAYER", context),
                self.parameterAsString(parameters, "RW_FIELD", context),
                context,
            )
            events = events_from_source(self.parameterAsSource(parameters, "EVENTS", context))
            access = access_from_source(self.parameterAsSource(parameters, "ACCESS", context))
            scenario = self.parameterAsSource(parameters, "SCENARIO_LAYER", context)
            scenario_rw = None
            if scenario is not None:
                field = (
                    "rw_no"
                    if "rw_no" in scenario.fields().names()
                    else self.parameterAsString(parameters, "RW_FIELD", context)
                )
                if field not in scenario.fields().names():
                    raise ValueError("Scenario list needs rw_no or the selected RW_FIELD")
                scenario_rw = {
                    number
                    for feature in scenario.getFeatures()
                    for number in parse_rw(str(value(feature, field) or ""))
                }
            rules = PriorityParameters(
                **{
                    target: self.parameterAsInt(parameters, key, context)
                    for target, key in (
                        ("episode_gap_days", "EPISODE_GAP_DAYS"),
                        ("rec_high", "REC_HIGH"),
                        ("rec_med", "REC_MED"),
                        ("depth_high_cm", "DEPTH_HIGH_CM"),
                    )
                }
            )
            run_id = self.parameterAsString(parameters, "RUN_ID", context) or str(uuid.uuid4())
            kelurahan = events[0].kelurahan if events else ""
            result = compute_priority(
                events,
                set(units),
                access=access,
                scenario_rw=scenario_rw,
                parameters=rules,
                kelurahan=kelurahan,
                run_id=run_id,
            )
            polygons = make_layer(
                "rw_priority",
                "MultiPolygon",
                PRIORITY_FIELDS,
                [asdict(row) for row in result.polygons],
                [units[row.rw_no] for row in result.polygons],
            )
            table = make_layer(
                "priority_table", "None", PRIORITY_FIELDS, [asdict(row) for row in result.table]
            )
            return {
                "OUTPUT_PRIORITY": output_layer(
                    self, parameters, "OUTPUT_PRIORITY", context, polygons, feedback
                ),
                "OUTPUT_PRIORITY_TABLE": output_layer(
                    self, parameters, "OUTPUT_PRIORITY_TABLE", context, table, feedback
                ),
            }
        except (ValueError, OSError, KeyError) as error:
            raise QgsProcessingException(str(error)) from error

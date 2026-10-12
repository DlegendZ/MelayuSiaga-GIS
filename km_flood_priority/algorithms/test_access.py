"""FR-2 verified-evidence pedestrian access with explicit UNKNOWN statuses."""

import json
from dataclasses import asdict

from qgis.core import (
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingOutputVariant,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from ..core.network import DEFAULT_EXCLUDED_HIGHWAY, build_graph, evaluate_access
from ..qgis_glue.fields import ACCESS_FIELDS, ROUTE_FIELDS
from ..qgis_glue.io import (
    event_dates,
    make_layer,
    origins_from_units,
    output_layer,
    read_closures,
    roads_from_source,
    rw_units,
    targets_from_source,
)
from .base import KMFloodAlgorithm


class TestAccessAlgorithm(KMFloodAlgorithm):
    NAME, TITLE = "test_access", "Test access to verified safe points"
    HELP = (
        "Reproject RW units, roads and point targets to EPSG:32748. Point-on-surface origins "
        "snap to existing vertices within the tolerance. Remove roads only for dated verified "
        "closures. Empty dates mean baseline only; ALL uses closure dates. Missing evidence "
        "produces UNKNOWN. Outputs include per-RW access, nonzero-length routes and graph stats."
    )

    def initAlgorithm(self, config=None):
        self.add_rw()
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "ROADS", "Road network", [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "SAFE_POINTS", "Safe-point evidence", [QgsProcessing.TypeVectorPoint], optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                "CLOSURES_CSV", "Dated closure evidence CSV", extension="csv", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "EVENT_DATES", "ISO dates (blank: baseline; ALL: closures)", "", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                "USE_UNVERIFIED_SAFE_POINTS", "Include unverified candidates (flagged)", False
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "EXCLUDED_HIGHWAY",
                "Excluded road types",
                ",".join(sorted(DEFAULT_EXCLUDED_HIGHWAY)),
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "SNAP_TOLERANCE_M",
                "Maximum snap distance (m)",
                QgsProcessingParameterNumber.Double,
                50,
                minValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT_ACCESS", "Access by RW and date", QgsProcessing.TypeVector
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OUTPUT_ROUTES", "Event or baseline routes", QgsProcessing.TypeVectorLine
            )
        )
        self.addOutput(QgsProcessingOutputVariant("OUTPUT_GRAPH_STATS", "Graph statistics"))

    def processAlgorithm(self, parameters, context, feedback):
        try:
            units = rw_units(
                self.parameterAsSource(parameters, "RW_LAYER", context),
                self.parameterAsString(parameters, "RW_FIELD", context),
                context,
            )
            roads = roads_from_source(self.parameterAsSource(parameters, "ROADS", context), context)
            targets = targets_from_source(
                self.parameterAsSource(parameters, "SAFE_POINTS", context), context
            )
            closures = read_closures(self.parameterAsFile(parameters, "CLOSURES_CSV", context))
            excluded = {
                item.strip().lower()
                for item in self.parameterAsString(parameters, "EXCLUDED_HIGHWAY", context).split(
                    ","
                )
                if item.strip()
            }
            result = evaluate_access(
                build_graph(roads, excluded),
                origins_from_units(units),
                targets,
                closures=closures,
                event_dates=event_dates(
                    self.parameterAsString(parameters, "EVENT_DATES", context), closures
                ),
                use_unverified_safe_points=self.parameterAsBool(
                    parameters, "USE_UNVERIFIED_SAFE_POINTS", context
                ),
                snap_tolerance_m=self.parameterAsDouble(parameters, "SNAP_TOLERANCE_M", context),
            )
            access = make_layer(
                "access_by_rw", "None", ACCESS_FIELDS, [asdict(row) for row in result.access]
            )
            routes = [route for route in result.routes if len(route.vertices) >= 2]
            route_layer = make_layer(
                "access_routes",
                "LineString",
                ROUTE_FIELDS,
                [asdict(route) for route in routes],
                [
                    QgsGeometry.fromPolylineXY([QgsPointXY(*point) for point in route.vertices])
                    for route in routes
                ],
            )
            feedback.pushInfo(json.dumps(result.graph_stats, sort_keys=True))
            return {
                "OUTPUT_ACCESS": output_layer(
                    self, parameters, "OUTPUT_ACCESS", context, access, feedback
                ),
                "OUTPUT_ROUTES": output_layer(
                    self, parameters, "OUTPUT_ROUTES", context, route_layer, feedback
                ),
                "OUTPUT_GRAPH_STATS": result.graph_stats,
            }
        except (ValueError, OSError, KeyError) as error:
            raise QgsProcessingException(str(error)) from error

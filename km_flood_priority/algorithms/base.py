"""Shared English Processing metadata and parameter definitions."""

from pathlib import Path

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtGui import QIcon

CLAIM_LIMITS = (
    "Results describe verification priority based on recorded events. "
    "No recorded event (≠ safe). Access without verified supporting evidence is UNKNOWN. "
    "The pedestrian graph is undirected and uses existing vertices, not a flood simulation."
)


class KMFloodAlgorithm(QgsProcessingAlgorithm):
    NAME = ""
    TITLE = ""
    GROUP = "2. Analysis"
    GROUP_ID = "analysis"
    HELP = ""

    def name(self):
        return self.NAME

    def displayName(self):
        return self.TITLE

    def group(self):
        return self.GROUP

    def groupId(self):
        return self.GROUP_ID

    def createInstance(self):
        return self.__class__()

    def shortHelpString(self):
        return f"{self.HELP}\n\n{CLAIM_LIMITS}"

    def icon(self):
        return QIcon(str(Path(__file__).parents[1] / "icon.svg"))

    def add_rw(self):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "RW_LAYER", "RW analysis units", [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField("RW_FIELD", "RW number field", "wadmrw", "RW_LAYER")
        )

    def add_area(self):
        self.addParameter(QgsProcessingParameterString("KELURAHAN", "Kelurahan", "KAMPUNG MELAYU"))
        self.addParameter(QgsProcessingParameterString("KECAMATAN", "Kecamatan", "JATINEGARA"))

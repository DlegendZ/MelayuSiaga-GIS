"""Processing provider with five offline recorded-event algorithms."""

from pathlib import Path

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .algorithms.compute_priority import ComputePriorityAlgorithm
from .algorithms.export_package import ExportPackageAlgorithm
from .algorithms.import_validate import ImportValidateAlgorithm
from .algorithms.run_pipeline import RunPipelineAlgorithm
from .algorithms.test_access import TestAccessAlgorithm


class KMFloodProvider(QgsProcessingProvider):
    def id(self):
        return "kmflood"

    def name(self):
        return "KM Flood Priority"

    def longName(self):
        return self.name()

    def icon(self):
        return QIcon(str(Path(__file__).parent / "icon.svg"))

    def loadAlgorithms(self):
        for algorithm in (
            RunPipelineAlgorithm,
            ImportValidateAlgorithm,
            TestAccessAlgorithm,
            ComputePriorityAlgorithm,
            ExportPackageAlgorithm,
        ):
            self.addAlgorithm(algorithm())

    def supportsNonFileBasedOutput(self):
        return True

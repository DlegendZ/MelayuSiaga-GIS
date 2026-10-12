"""QGIS entry points, idempotent provider lifecycle, and three English menu actions."""

from pathlib import Path

from qgis.core import QgsApplication, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QAction, QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QMessageBox

from .provider import KMFloodProvider
from .qgis_glue.styles import apply_style


class KMFloodPriorityPlugin:
    MENU = "&KM Flood Priority"

    def __init__(self, iface):
        self.iface, self.provider, self.actions = iface, None, []

    def initProcessing(self):
        if self.provider is None:
            self.provider = KMFloodProvider()
            if not QgsApplication.processingRegistry().addProvider(self.provider):
                self.provider = None
                raise RuntimeError("KM Flood Priority provider could not be registered")

    def initGui(self):
        self.initProcessing()
        if self.iface is None or self.actions:
            return
        icon = QIcon(str(Path(__file__).parent / "icon.svg"))
        for text, callback in (
            ("Run full pipeline…", self.run_pipeline),
            ("Load sample data", self.load_sample),
            ("Help", self.help),
        ):
            action = QAction(icon, text, self.iface.mainWindow())
            action.triggered.connect(callback)
            self.iface.addPluginToMenu(self.MENU, action)
            self.actions.append(action)

    def unload(self):
        if self.iface is not None:
            for action in self.actions:
                self.iface.removePluginMenu(self.MENU, action)
                action.deleteLater()
        self.actions = []
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def run_pipeline(self, checked=False):
        import processing

        processing.execAlgorithmDialog("kmflood:run_pipeline")

    def help(self, checked=False):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(__file__).parent / "help/index.html")))

    def load_sample(self, checked=False):
        path = Path(__file__).parent / "sample_data/inputs.gpkg"
        if not path.exists():
            QMessageBox.information(
                self.iface.mainWindow(),
                "Sample data unavailable",
                "This build excludes real sample data while redistribution terms "
                "are unresolved. Prepare inputs.gpkg using the repository guide.",
            )
            return
        loaded = []
        for name in ("rw", "kelurahan_boundary", "roads", "buildings", "safe_points"):
            layer = QgsVectorLayer(f"{path}|layername={name}", name, "ogr")
            if not layer.isValid():
                QMessageBox.warning(
                    self.iface.mainWindow(), "Sample data error", f"Could not load {name}"
                )
                return
            if name in {"kelurahan_boundary", "roads", "safe_points"}:
                apply_style(layer, name)
            loaded.append(layer)
        QgsProject.instance().addMapLayers(loaded)
        boundary = next(layer for layer in loaded if layer.name() == "kelurahan_boundary")
        self.iface.mapCanvas().setExtent(boundary.extent())
        self.iface.mapCanvas().refresh()

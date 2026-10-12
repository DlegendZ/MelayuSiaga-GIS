"""Provider registration and menu removal across repeated QGIS reloads."""

from qgis.core import QgsApplication, QgsProject
from qgis.PyQt.QtWidgets import QMainWindow, QMessageBox

from km_flood_priority import classFactory


class Interface:
    def __init__(self):
        self.window = QMainWindow()
        self.menu = []

    def mainWindow(self):
        return self.window

    def addPluginToMenu(self, menu, action):
        self.menu.append((menu, action))

    def removePluginMenu(self, menu, action):
        self.menu.remove((menu, action))


def test_plugin_reload_removes_all_actions_and_provider(qgis_runtime, monkeypatch):
    registry = QgsApplication.processingRegistry()
    existing = registry.providerById("kmflood")
    registry.removeProvider(existing)
    iface = Interface()
    messages = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args: messages.append(args[2]))
    for _ in range(2):
        plugin = classFactory(iface)
        plugin.initGui()
        plugin.initGui()
        assert len(iface.menu) == 3
        assert registry.providerById("kmflood") is plugin.provider
        before = set(QgsProject.instance().mapLayers())
        plugin.load_sample()
        assert set(QgsProject.instance().mapLayers()) == before
        assert "redistribution permission" in messages[-1]
        assert "#reproduce-from-scratch" in messages[-1]
        plugin.unload()
        plugin.unload()
        assert iface.menu == [] and registry.providerById("kmflood") is None

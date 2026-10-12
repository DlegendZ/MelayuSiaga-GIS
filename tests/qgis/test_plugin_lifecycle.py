"""Provider registration and menu removal across repeated QGIS reloads."""

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMainWindow

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


def test_plugin_reload_removes_all_actions_and_provider(qgis_runtime):
    registry = QgsApplication.processingRegistry()
    existing = registry.providerById("kmflood")
    registry.removeProvider(existing)
    iface = Interface()
    for _ in range(2):
        plugin = classFactory(iface)
        plugin.initGui()
        plugin.initGui()
        assert len(iface.menu) == 3
        assert registry.providerById("kmflood") is plugin.provider
        plugin.unload()
        plugin.unload()
        assert iface.menu == [] and registry.providerById("kmflood") is None

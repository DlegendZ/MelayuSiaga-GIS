"""KM Flood Priority: recorded-event verification priority for QGIS.

Importing this package does not load QGIS; the pure Python core is usable independently.
"""

__version__ = "1.0.0"


def classFactory(iface):
    """QGIS plugin entry point, completed during Phase 3."""
    from .plugin import KMFloodPriorityPlugin

    return KMFloodPriorityPlugin(iface)

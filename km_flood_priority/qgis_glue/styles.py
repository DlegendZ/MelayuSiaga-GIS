"""Apply bundled QML and embed default styles in a result GeoPackage."""

from pathlib import Path

from qgis.core import QgsMapLayer

STYLE_DIR = Path(__file__).parents[1] / "styles"
SPATIAL_STYLES = {"rw_priority", "access_routes", "safe_points", "roads", "kelurahan_boundary"}


def apply_style(layer, name):
    if name not in SPATIAL_STYLES:
        return
    message, success = layer.loadNamedStyle(str(STYLE_DIR / f"{name}.qml"))
    if not success:
        raise ValueError(f"Could not load bundled {name} style: {message}")


def save_default_style(layer, name):
    apply_style(layer, name)
    description = (
        "KM Flood Priority: recorded-event verification; missing access evidence is UNKNOWN"
    )
    if hasattr(layer, "saveStyleToDatabaseV2"):
        flags, error = layer.saveStyleToDatabaseV2(name, description, True, "")

        # Qt6 exposes these as Enum values rather than the Qt5 integer wrappers.
        def bits(item):
            return item.value if hasattr(item, "value") else int(item)

        fatal = bits(QgsMapLayer.SaveStyleResult.QmlGenerationFailed) | bits(
            QgsMapLayer.SaveStyleResult.DatabaseWriteFailed
        )
        if bits(flags) & fatal:
            raise ValueError(f"Could not embed {name} style: {error}")
    else:
        error = layer.saveStyleToDatabase(name, description, True, "")
        if error:
            raise ValueError(f"Could not embed {name} style: {error}")

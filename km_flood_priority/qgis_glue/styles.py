"""Apply bundled QML and embed default styles in a result GeoPackage."""

from pathlib import Path

from qgis.core import QgsMapLayer, QgsProcessingLayerPostProcessorInterface
from qgis.PyQt import sip

STYLE_DIR = Path(__file__).parents[1] / "styles"
SPATIAL_STYLES = {"rw_priority", "access_routes", "safe_points", "roads", "kelurahan_boundary"}


class PackageStylePostProcessor(QgsProcessingLayerPostProcessorInterface):
    """Restore embedded styles after Processing's GUI result loader has finished."""

    # A worker's Python context wrapper can disappear before GUI completion.
    # C++ owns each processor, but SIP still needs this module-level reference
    # to dispatch its Python virtual method. Keep separate callbacks per output.
    _instances = []

    @classmethod
    def create(cls, final_package, name):
        # Context destruction deletes the C++ objects. Drop their stale wrappers
        # on the next run without releasing callbacks for a still-pending model.
        cls._instances[:] = [item for item in cls._instances if not sip.isdeleted(item)]
        processor = cls(final_package, name)
        cls._instances.append(processor)
        return processor

    def __init__(self, final_package, name):
        super().__init__()
        self.uri = f"{final_package}|layername={name}"
        self.name = name

    def postProcessLayer(self, layer, context, feedback):
        feedback.pushInfo(f"KM Flood Priority: postProcessLayer({self.name}) from {self.uri}")
        if layer.source() != self.uri:
            layer.setDataSource(self.uri, self.name, "ogr")
        message, success = layer.loadDefaultStyle()
        if not success:
            feedback.reportError(f"Could not load embedded {self.name} style: {message}")
            return
        layer.triggerRepaint()
        feedback.pushInfo(
            f"KM Flood Priority: restored {self.name} style ({layer.renderer().type()})"
        )


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

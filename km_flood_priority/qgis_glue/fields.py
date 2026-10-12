"""Field schemas and Qt5/Qt6-safe attribute conversion."""

from datetime import date

from qgis.core import QgsField, QgsFields
from qgis.PyQt.QtCore import QDate, QMetaType

from ..core.schema import SAFE_POINT_COLUMNS, SOURCE_COLUMNS, PriorityRecord

EVENT_FIELDS = [
    ("event_uid", "str"),
    ("event_id", "str"),
    ("source_id", "str"),
    ("source_ref", "str"),
    ("event_date", "date"),
    ("year", "int"),
    ("kelurahan", "str"),
    ("kecamatan", "str"),
    ("rw_no", "int"),
    ("rt_raw", "str"),
    ("address_raw", "str"),
    ("depth_min_cm", "int"),
    ("depth_max_cm", "int"),
    ("affected_kk", "int"),
    ("affected_people", "int"),
    ("location_confidence", "str"),
    ("verified", "str"),
    ("duplicate_of", "str"),
    ("notes", "str"),
]
ISSUE_FIELDS = [
    (name, "int" if name == "row_number" else "str")
    for name in ("issue_id", "event_id", "row_number", "field", "severity", "code", "message")
]
ACCESS_FIELDS = [
    ("rw_no", "int"),
    ("event_date", "str"),
    ("access_status", "str"),
    ("status_reason", "str"),
    ("nearest_sp_id", "str"),
    ("route_length_m", "real"),
    ("baseline_length_m", "real"),
    ("targets_verified", "str"),
    ("removed_edges", "int"),
]
ROUTE_FIELDS = [("rw_no", "int"), ("event_date", "str"), ("access_status", "str")]
_PRIORITY_INTS = {
    "rw_no",
    "n_records",
    "n_episodes",
    "n_years",
    "max_depth_cm",
    "depth_known_n",
    "max_affected_kk",
    "rank_in_class",
}
PRIORITY_FIELDS = [
    (
        name,
        "int"
        if name in _PRIORITY_INTS
        else "date"
        if name in {"first_date", "last_date"}
        else "real"
        if name == "low_conf_share"
        else "str",
    )
    for name in PriorityRecord.__dataclass_fields__
]
SOURCE_FIELDS = [(name, "str") for name in SOURCE_COLUMNS]
SAFE_FIELDS = [
    (name, "int" if name == "capacity" else "real" if name in {"lon", "lat"} else "str")
    for name in SAFE_POINT_COLUMNS
]
RUN_FIELDS = [
    (name, "str")
    for name in (
        "run_id",
        "timestamp",
        "plugin_version",
        "qgis_version",
        "parameters_json",
        "years_covered",
    )
]


def make_fields(specification):
    types = {
        "str": QMetaType.Type.QString,
        "int": QMetaType.Type.Int,
        "real": QMetaType.Type.Double,
        "date": QMetaType.Type.QDate,
    }
    fields = QgsFields()
    for name, kind in specification:
        fields.append(QgsField(name, types[kind]))
    return fields


def attributes(record, fields):
    values = []
    for field in fields:
        value = record.get(field.name())
        if isinstance(value, date):
            value = QDate(value.year, value.month, value.day)
        values.append(value)
    return values

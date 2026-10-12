"""Normative field names and standard-library data models (spec §7)."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

EVENT_COLUMNS = (
    "event_id",
    "source_id",
    "source_ref",
    "event_date",
    "kota",
    "kecamatan",
    "kelurahan",
    "rw_raw",
    "rt_raw",
    "address_raw",
    "depth_raw",
    "affected_rt_count",
    "affected_kk",
    "affected_people",
    "duration_raw",
    "location_confidence",
    "verified",
    "notes",
)
EVENT_REQUIRED = (
    "event_id",
    "source_id",
    "source_ref",
    "event_date",
    "kota",
    "kecamatan",
    "kelurahan",
    "location_confidence",
    "verified",
)
SOURCE_COLUMNS = (
    "source_id",
    "title",
    "publisher",
    "url",
    "retrieved_on",
    "license_terms",
    "format",
    "coverage_years",
    "notes",
)
CLOSURE_COLUMNS = (
    "closure_id",
    "event_date",
    "road_ref_type",
    "road_ref",
    "verified",
    "source_id",
    "source_ref",
    "notes",
)
SAFE_POINT_COLUMNS = (
    "sp_id",
    "name",
    "sp_type",
    "capacity",
    "lon",
    "lat",
    "verified",
    "source_id",
    "source_ref",
    "notes",
)
ISSUE_CODES = frozenset(
    {
        "missing_column",
        "bad_date",
        "rw_not_in_layer",
        "confidence_mismatch",
        "depth_missing",
        "depth_unparsed",
        "depth_implausible",
        "unknown_source",
        "invalid_confidence",
        "dropped_other_area",
        "duplicate",
    }
)


class LocationConfidence(str, Enum):
    ADDRESS = "ADDRESS"
    RT = "RT"
    RW = "RW"
    RW_INFERRED = "RW_INFERRED"
    KELURAHAN = "KELURAHAN"
    UNKNOWN = "UNKNOWN"


COUNTABLE_CONFIDENCE = frozenset({"ADDRESS", "RT", "RW", "RW_INFERRED"})


class AccessStatus(str, Enum):
    REACHABLE = "REACHABLE"
    CUT_OFF = "CUT_OFF"
    UNKNOWN = "UNKNOWN"


class PriorityClass(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    VERIFY = "VERIFY"
    NO_RECORD = "NO_RECORD"


@dataclass(frozen=True)
class Event:
    event_uid: str
    event_id: str
    source_id: str
    source_ref: str
    event_date: date
    kelurahan: str
    kecamatan: str
    rw_no: int | None
    location_confidence: str
    verified: str
    rt_raw: str = ""
    address_raw: str = ""
    depth_min_cm: int | None = None
    depth_max_cm: int | None = None
    affected_kk: int | None = None
    affected_people: int | None = None
    duplicate_of: str | None = None
    row_number: int = 0

    @property
    def year(self) -> int:
        return self.event_date.year


@dataclass(frozen=True)
class ValidationIssue:
    issue_id: str
    event_id: str
    row_number: int
    field: str
    severity: str
    code: str
    message: str


@dataclass
class ImportResult:
    events: list[Event]
    issues: list[ValidationIssue]
    summary: dict


@dataclass(frozen=True)
class Closure:
    closure_id: str
    event_date: date
    road_ref_type: str
    road_ref: str
    verified: str = "N"
    source_id: str = ""
    source_ref: str = ""
    notes: str = ""


@dataclass(frozen=True)
class Road:
    osm_id: str
    vertices: tuple[tuple[float, float], ...]
    highway: str = "residential"
    name: str = ""


@dataclass(frozen=True)
class SafePoint:
    sp_id: str
    coordinates: tuple[float, float]
    verified: str = "N"
    name: str = ""


@dataclass(frozen=True)
class Origin:
    rw_no: int
    coordinates: tuple[float, float]


@dataclass(frozen=True)
class AccessRecord:
    rw_no: int
    event_date: str
    access_status: str
    status_reason: str
    nearest_sp_id: str | None = None
    route_length_m: float | None = None
    baseline_length_m: float | None = None
    targets_verified: str = "Y"
    removed_edges: int = 0


@dataclass(frozen=True)
class Route:
    rw_no: int
    event_date: str
    access_status: str
    vertices: tuple[tuple[float, float], ...]


@dataclass
class AccessResult:
    access: list[AccessRecord]
    routes: list[Route]
    graph_stats: dict


@dataclass(frozen=True)
class PriorityParameters:
    episode_gap_days: int = 2
    rec_high: int = 3
    rec_med: int = 2
    depth_high_cm: int = 50

    def __post_init__(self):
        if self.episode_gap_days < 0 or self.depth_high_cm < 0:
            raise ValueError("Episode gap and depth threshold must be non-negative")
        if self.rec_med < 1 or self.rec_high < self.rec_med:
            raise ValueError("Recurrence thresholds must satisfy 1 <= REC_MED <= REC_HIGH")


@dataclass
class PriorityRecord:
    rw_no: int | None
    rw_label: str
    kelurahan: str
    n_records: int = 0
    n_episodes: int = 0
    n_years: int = 0
    first_date: date | None = None
    last_date: date | None = None
    max_depth_cm: int | None = None
    depth_known_n: int = 0
    max_affected_kk: int | None = None
    low_conf_share: float = 0.0
    access_worst: str = "NOT_RUN"
    priority_class: str = "NO_RECORD"
    needs_field_check: str = "Y"
    class_reason: str = ""
    rank_in_class: int | None = None
    source_refs: str = ""
    scenario_flag: str = "NA"
    run_id: str = ""


@dataclass
class PriorityResult:
    polygons: list[PriorityRecord] = field(default_factory=list)
    table: list[PriorityRecord] = field(default_factory=list)

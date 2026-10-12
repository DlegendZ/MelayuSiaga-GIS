from datetime import date

import pytest

from km_flood_priority.core.normalize import normalize_name, parse_depth, parse_rw
from km_flood_priority.core.validation import NoValidRowsError, SchemaError


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("RW 04", [4]),
        ("04/05", [4, 5]),
        ("4 dan 5", [4, 5]),
        ("", []),
        ("004", [4]),
        ("04/04", [4]),
        (None, []),
    ],
)
def test_rw_normalization(raw, expected):
    assert parse_rw(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("30-50 cm", (30, 50)),
        ("30 – 50 cm", (30, 50)),
        ("0.5 m", (50, 50)),
        ("40", (40, 40)),
        ("50cm", (50, 50)),
        ("tinggi", (None, None)),
        ("", (None, None)),
        (None, (None, None)),
        ("0,5 m", (50, 50)),
        ("50-30 cm", (None, None)),
        ("-40 cm", (None, None)),
        ("0.3-0.5 m", (30, 50)),
    ],
)
def test_depth_normalization(raw, expected):
    assert parse_depth(raw) == expected


@pytest.mark.parametrize("name", ["Kp. Melayu", " KAMPUNG  MELAYU ", "kp melayu"])
def test_kelurahan_alias(name):
    assert normalize_name(name) == "KAMPUNG MELAYU"


def test_explode_and_dates(raw_event, importer):
    result = importer([{**raw_event, "rw_raw": "04/05"}])
    assert [e.event_uid for e in result.events] == ["TEST-A#4", "TEST-A#5"]
    assert result.events[0].event_date == date(2025, 3, 4)
    assert result.events[0].year == 2025
    assert result.summary["exploded_rows"] == 2


def test_missing_column_fails(raw_event, importer):
    del raw_event["event_date"]
    with pytest.raises(SchemaError, match="event_date"):
        importer([raw_event])


def test_dropped_area_does_not_match_other_district(raw_event, importer):
    result = importer([raw_event, {**raw_event, "kecamatan": "OTHER DISTRICT"}])
    assert result.summary["rows_dropped_area"] == 1
    assert any(i.code == "dropped_other_area" for i in result.issues)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("event_date", "2025-02-30", "bad_date"),
        ("event_date", "20250304", "bad_date"),
        ("location_confidence", "STREET", "invalid_confidence"),
        ("source_id", "UNREGISTERED", "unknown_source"),
    ],
)
def test_row_errors_excluded(raw_event, importer, field, value, code):
    result = importer([raw_event, {**raw_event, field: value}])
    assert len(result.events) == 1
    assert result.summary["errors"] == 1
    issue = next(i for i in result.issues if i.code == code)
    assert issue.row_number == 3


def test_zero_valid_rows_fails_with_report(raw_event, importer):
    with pytest.raises(NoValidRowsError) as exc:
        importer([{**raw_event, "event_date": "invalid"}])
    assert exc.value.result.issues[0].code == "bad_date"


def test_unknown_rw_preserved_as_unassigned(raw_event, importer):
    result = importer([{**raw_event, "rw_raw": "04/99"}])
    assert [e.rw_no for e in result.events] == [4, None]
    assert result.events[1].event_uid == "TEST-A#99"
    assert result.summary["rw_unassigned"] == 1
    assert any(i.code == "rw_not_in_layer" for i in result.issues)


def test_coarse_row_kept_and_confidence_checked(raw_event, importer):
    result = importer([{**raw_event, "rw_raw": ""}])
    assert result.events[0].rw_no is None
    assert any(i.code == "confidence_mismatch" for i in result.issues)


def test_coarse_confidence_no_warning(raw_event, importer):
    result = importer([{**raw_event, "rw_raw": "", "location_confidence": "KELURAHAN"}])
    assert not any(i.code == "confidence_mismatch" for i in result.issues)


@pytest.mark.parametrize(
    "raw,code",
    [
        ("", "depth_missing"),
        ("tinggi", "depth_unparsed"),
        ("650", "depth_implausible"),
    ],
)
def test_depth_issues(raw_event, importer, raw, code):
    result = importer([{**raw_event, "depth_raw": raw}])
    assert any(i.code == code for i in result.issues)
    if raw == "650":
        assert result.events[0].depth_max_cm == 650


def test_cross_source_dedupe_depth_wins(raw_event, importer):
    result = importer(
        [
            {**raw_event, "depth_raw": ""},
            {**raw_event, "event_id": "OTHER-A", "source_id": "OTHER"},
        ]
    )
    assert result.events[0].duplicate_of == "OTHER-A#4"
    assert result.events[1].duplicate_of is None
    assert result.summary["duplicates"] == 1


def test_source_priority_overrides_depth(raw_event, importer):
    result = importer(
        [
            {**raw_event, "depth_raw": ""},
            {**raw_event, "event_id": "OTHER-A", "source_id": "OTHER"},
        ],
        source_priority=["SYNTHETIC", "OTHER"],
    )
    assert result.events[1].duplicate_of == "TEST-A#4"


def test_same_source_rows_are_not_deduplicated(raw_event, importer):
    result = importer([raw_event, {**raw_event, "event_id": "TEST-D"}])
    assert all(e.duplicate_of is None for e in result.events)


def test_unassigned_rows_follow_cross_source_dedupe_rule(raw_event, importer):
    result = importer(
        [
            {**raw_event, "rw_raw": "", "location_confidence": "KELURAHAN"},
            {**raw_event, "event_id": "OTHER-A", "source_id": "OTHER", "rw_raw": "99"},
        ]
    )
    assert result.events[1].duplicate_of == "TEST-A#unassigned"


def test_optional_impact_numbers(raw_event, importer):
    result = importer([{**raw_event, "affected_kk": "12", "affected_people": "unknown"}])
    assert result.events[0].affected_kk == 12
    assert result.events[0].affected_people is None


def test_output_is_deterministic(raw_event, importer):
    assert importer([raw_event]) == importer([raw_event])

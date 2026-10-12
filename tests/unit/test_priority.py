from dataclasses import replace
from datetime import date

import pytest

from km_flood_priority.core.episodes import group_episodes
from km_flood_priority.core.priority import compute_priority
from km_flood_priority.core.schema import AccessRecord, Event, PriorityParameters


def event(rw=4, when="2025-03-04", depth=None, confidence="RW", **kwargs):
    return Event(
        f"TEST-{rw}-{when}#{rw}",
        "TEST",
        "SYNTHETIC",
        "row 1",
        date.fromisoformat(when),
        "TESTVILLE",
        "TEST DISTRICT",
        rw,
        confidence,
        "N",
        depth_max_cm=depth,
        **kwargs,
    )


def recurrent(rw=4, depth=None, confidence="RW"):
    return [
        event(rw, when, depth, confidence) for when in ("2020-03-04", "2023-03-04", "2025-03-04")
    ]


def access(status, rw=4, when="2025-03-04", reason="test"):
    return AccessRecord(rw, when, status, reason)


@pytest.mark.parametrize("gap,expected", [(2, 2), (0, 3)])
def test_episode_gap(gap, expected):
    dates = [date(2025, 3, 4), date(2025, 3, 5), date(2025, 7, 7)]
    assert len(group_episodes(dates, gap)) == expected


def test_episode_distinct_dates_and_chain():
    dates = [date(2025, 3, d) for d in (8, 4, 6, 4)]
    assert len(group_episodes(dates, 2)) == 1
    assert group_episodes([], 2) == []


def test_negative_gap_rejected():
    with pytest.raises(ValueError):
        group_episodes([], -1)


@pytest.mark.parametrize(
    "records,rows,expected",
    [
        (recurrent(depth=50), None, "HIGH"),
        (recurrent(), [access("CUT_OFF")], "HIGH"),
        (recurrent(), None, "MEDIUM"),
        ([event(depth=50)], None, "MEDIUM"),
        ([event()], [access("CUT_OFF")], "MEDIUM"),
        ([event(depth=30)], None, "VERIFY"),
        ([], None, "NO_RECORD"),
    ],
)
def test_normative_class_rules(records, rows, expected):
    result = compute_priority(records, [4], access=rows, kelurahan="TESTVILLE")
    assert result.polygons[0].priority_class == expected


def test_coarse_and_duplicate_records_not_counted():
    records = [
        event(),
        event(None, confidence="KELURAHAN"),
        replace(event(4, "2025-07-07"), duplicate_of="other"),
        event(5, confidence="KELURAHAN"),
    ]
    result = compute_priority(records, [4, 5], kelurahan="TESTVILLE")
    assert [row.n_records for row in result.polygons] == [1, 0]
    assert result.table[-1].rw_no is None
    assert result.table[-1].n_records == 1
    assert result.table[-1].rw_label == "Unassigned (kelurahan-level)"
    assert result.table[-1].rank_in_class is None


@pytest.mark.parametrize(
    "depth,confidence,status,expected",
    [
        (50, "RW", "REACHABLE", "N"),
        (None, "RW", "REACHABLE", "Y"),
        (50, "RW_INFERRED", "REACHABLE", "Y"),
        (50, "RW", "UNKNOWN", "Y"),
        (50, "RW", None, "Y"),
    ],
)
def test_needs_field_check(depth, confidence, status, expected):
    rows = None if status is None else [access(status)]
    row = compute_priority(
        [event(depth=depth, confidence=confidence)], [4], access=rows, kelurahan="TESTVILLE"
    ).polygons[0]
    assert row.needs_field_check == expected


def test_low_conf_share_half_boundary():
    records = [event(depth=50), event(4, "2025-07-07", 50, "RW_INFERRED")]
    row = compute_priority(records, [4], access=[access("REACHABLE")]).polygons[0]
    assert row.low_conf_share == 0.5
    assert row.needs_field_check == "Y"


def test_worst_event_access_and_baseline_ignored():
    rows = [
        access("UNKNOWN", when="BASELINE"),
        access("REACHABLE"),
        access("UNKNOWN", when="2025-07-07"),
        access("CUT_OFF", when="2025-09-01"),
    ]
    assert compute_priority([event()], [4], access=rows).polygons[0].access_worst == "CUT_OFF"
    assert compute_priority([event()], [4], access=rows[:2]).polygons[0].access_worst == "REACHABLE"
    assert compute_priority([event()], [4], access=[]).polygons[0].access_worst == "UNKNOWN"


def test_ranking_nulls_last_and_dates_descending():
    records = [
        event(4, "2024-01-01", 20),
        event(5, "2025-01-01", 20),
        event(6, "2025-01-01"),
        event(7, "2025-01-01", 10),
    ]
    rows = compute_priority(records, [4, 5, 6, 7]).polygons
    assert {r.rw_no: r.rank_in_class for r in rows} == {4: 2, 5: 1, 6: 4, 7: 3}


def test_ranking_episode_count_first():
    rows = compute_priority(
        recurrent(4, 50) + recurrent(5, 80) + [event(4, "2021-01-01", 50)], [4, 5]
    ).polygons
    assert [r.rank_in_class for r in rows] == [1, 2]


def test_scenario_is_only_comparator():
    result = compute_priority([event()], [4, 5], scenario_rw={5})
    assert [r.scenario_flag for r in result.polygons] == ["NO", "YES"]
    assert [r.priority_class for r in result.polygons] == ["VERIFY", "NO_RECORD"]


def test_aggregate_fields_and_reason():
    records = [
        event(when="2020-03-04", depth=50, affected_kk=12),
        event(when="2025-03-04", depth=80, affected_kk=10),
    ]
    row = compute_priority(
        records,
        [4],
        access=[access("UNKNOWN", reason="no_verified_safe_points")],
        run_id="run-test",
    ).polygons[0]
    assert (row.n_records, row.n_episodes, row.n_years, row.depth_known_n) == (2, 2, 2, 2)
    assert row.max_depth_cm == 80
    assert row.max_affected_kk == 12
    assert row.first_date == date(2020, 3, 4)
    assert "no verified safe points" in row.class_reason
    assert row.source_refs == "SYNTHETIC:row 1"
    assert row.run_id == "run-test"


def test_no_record_label_claim_limit():
    row = compute_priority([], [4]).polygons[0]
    assert "No recorded event (≠ safe)" in row.class_reason


@pytest.mark.parametrize(
    "kwargs",
    [
        {"episode_gap_days": -1},
        {"depth_high_cm": -1},
        {"rec_med": 0},
        {"rec_high": 1, "rec_med": 2},
    ],
)
def test_invalid_thresholds(kwargs):
    with pytest.raises(ValueError):
        PriorityParameters(**kwargs)


def test_custom_thresholds_and_no_mutation():
    records = recurrent(depth=30)
    before = list(records)
    row = compute_priority(records, [4], parameters=PriorityParameters(depth_high_cm=30)).polygons[
        0
    ]
    assert row.priority_class == "HIGH"
    assert records == before

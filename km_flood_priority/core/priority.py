"""FR-3 aggregation and transparent recorded-event verification classification."""

from .episodes import group_episodes
from .schema import (
    COUNTABLE_CONFIDENCE,
    PriorityParameters,
    PriorityRecord,
    PriorityResult,
)

ACCESS_ORDER = {"REACHABLE": 0, "UNKNOWN": 1, "CUT_OFF": 2}


def classify(n_records, n_episodes, max_depth_cm, access_worst, parameters):
    if n_records == 0:
        return "NO_RECORD"
    depth_high = max_depth_cm is not None and max_depth_cm >= parameters.depth_high_cm
    cut_off = access_worst == "CUT_OFF"
    if n_episodes >= parameters.rec_high and (depth_high or cut_off):
        return "HIGH"
    if n_episodes >= parameters.rec_med or depth_high or cut_off:
        return "MEDIUM"
    return "VERIFY"


def _aggregate(records, rw_no, kelurahan, run_id):
    depths = [e.depth_max_cm for e in records if e.depth_max_cm is not None]
    impacts = [e.affected_kk for e in records if e.affected_kk is not None]
    dates = sorted({e.event_date for e in records})
    return PriorityRecord(
        rw_no=rw_no,
        rw_label=f"RW {rw_no:02d}" if rw_no is not None else "Unassigned (kelurahan-level)",
        kelurahan=kelurahan,
        n_records=len(records),
        n_years=len({e.year for e in records}),
        first_date=dates[0] if dates else None,
        last_date=dates[-1] if dates else None,
        max_depth_cm=max(depths) if depths else None,
        depth_known_n=len(depths),
        max_affected_kk=max(impacts) if impacts else None,
        low_conf_share=sum(e.location_confidence == "RW_INFERRED" for e in records) / len(records)
        if records
        else 0.0,
        source_refs=";".join(sorted({f"{e.source_id}:{e.source_ref}" for e in records})),
        run_id=run_id,
    )


def compute_priority(
    events,
    rw_numbers,
    *,
    access=None,
    scenario_rw=None,
    parameters=None,
    kelurahan="KAMPUNG MELAYU",
    run_id="",
) -> PriorityResult:
    parameters = parameters or PriorityParameters()
    canonical = [e for e in events if e.duplicate_of is None]
    access_rows = None if access is None else list(access)
    rows = []
    for rw_no in sorted(set(rw_numbers)):
        records = [
            e
            for e in canonical
            if e.rw_no == rw_no and e.location_confidence in COUNTABLE_CONFIDENCE
        ]
        row = _aggregate(records, rw_no, kelurahan, run_id)
        row.n_episodes = len(
            group_episodes([e.event_date for e in records], parameters.episode_gap_days)
        )
        event_access = (
            []
            if access_rows is None
            else [a for a in access_rows if a.rw_no == rw_no and a.event_date != "BASELINE"]
        )
        worst = max(event_access, key=lambda a: ACCESS_ORDER[a.access_status], default=None)
        row.access_worst = (
            worst.access_status if worst else ("NOT_RUN" if access_rows is None else "UNKNOWN")
        )
        row.priority_class = classify(
            row.n_records, row.n_episodes, row.max_depth_cm, row.access_worst, parameters
        )
        row.needs_field_check = (
            "Y"
            if (
                row.depth_known_n == 0
                or row.low_conf_share >= 0.5
                or row.access_worst in {"UNKNOWN", "NOT_RUN"}
            )
            else "N"
        )
        row.scenario_flag = (
            "NA" if scenario_rw is None else ("YES" if rw_no in scenario_rw else "NO")
        )
        if not records:
            row.class_reason = "No recorded event (≠ safe); field verification required"
        else:
            years = sorted({e.year for e in records})
            year_text = str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
            depth = (
                "depth unrecorded"
                if row.max_depth_cm is None
                else (f"max depth {row.max_depth_cm} cm")
            )
            reason = f" ({worst.status_reason.replace('_', ' ')})" if worst else ""
            row.class_reason = (
                f"{row.n_episodes} episodes ({year_text}), {depth}, "
                f"access {row.access_worst}{reason}"
            )
        rows.append(row)
    for class_name in {row.priority_class for row in rows}:
        in_class = sorted(
            [row for row in rows if row.priority_class == class_name],
            key=lambda row: (
                -row.n_episodes,
                row.max_depth_cm is None,
                -(row.max_depth_cm or 0),
                -row.last_date.toordinal() if row.last_date else 0,
                row.rw_no,
            ),
        )
        for rank, row in enumerate(in_class, start=1):
            row.rank_in_class = rank
    unassigned = _aggregate([e for e in canonical if e.rw_no is None], None, kelurahan, run_id)
    unassigned.priority_class = "VERIFY" if unassigned.n_records else "NO_RECORD"
    unassigned.class_reason = (
        f"{unassigned.n_records} unassigned canonical records; excluded from RW classification"
    )
    return PriorityResult(rows, [*rows, unassigned])

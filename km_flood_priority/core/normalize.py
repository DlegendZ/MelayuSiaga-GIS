"""FR-1 normalization and cross-source deduplication, with no GIS dependencies."""

import re
from collections import defaultdict
from dataclasses import replace
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .schema import EVENT_REQUIRED, Event, ImportResult, LocationConfidence
from .validation import NoValidRowsError, add_issue, require_columns, summarize


def normalize_name(value: str | None) -> str:
    text = re.sub(r"\bKP\.?(?=\s|$)\s*", "KAMPUNG ", (value or "").upper())
    return " ".join(text.split())


def parse_rw(value: str | None) -> list[int]:
    return list(dict.fromkeys(int(n) for n in re.findall(r"\d+", value or "")))


def parse_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected an ISO date YYYY-MM-DD")
    return date.fromisoformat(value)


def parse_depth(value: str | None) -> tuple[int | None, int | None]:
    text = (value or "").strip().lower().replace("–", "-").replace("—", "-")
    text = text.replace(",", ".")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(cm|m)?", text)
    if not match:
        return None, None
    lo, hi, unit = match.groups()
    factor = 100 if unit == "m" else 1
    values = tuple(
        int((Decimal(n) * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        for n in (lo, hi or lo)
    )
    return values if values[0] <= values[1] else (None, None)


def _optional_int(value):
    try:
        number = int(value)
        return number if number >= 0 else None
    except (ValueError, TypeError):
        return None


def deduplicate(events: list[Event], source_priority=()) -> list[Event]:
    groups = defaultdict(list)
    for index, event in enumerate(events):
        groups[(event.event_date, event.rw_no)].append(index)
    ranks = {source: rank for rank, source in enumerate(source_priority)}
    result = list(events)
    for indices in groups.values():
        if len({events[i].source_id for i in indices}) < 2:
            continue

        def key(index):
            event = events[index]
            return (ranks.get(event.source_id, len(ranks)), event.depth_max_cm is None, index)

        chosen = min(indices, key=key)
        canonical = events[chosen]
        for index in indices:
            if events[index].source_id != canonical.source_id:
                result[index] = replace(events[index], duplicate_of=canonical.event_uid)
    return result


def import_events(
    rows,
    *,
    rw_numbers,
    source_ids,
    columns=None,
    kelurahan="KAMPUNG MELAYU",
    kecamatan="JATINEGARA",
    source_priority=(),
) -> ImportResult:
    rows = list(rows)
    require_columns(columns if columns is not None else (rows[0] if rows else []), EVENT_REQUIRED)
    events, issues = [], []
    kept = dropped = exploded = 0
    area, district = normalize_name(kelurahan), normalize_name(kecamatan)
    confidence_values = {item.value for item in LocationConfidence}
    for row_number, row in enumerate(rows, start=2):
        require_columns(row, EVENT_REQUIRED)
        event_id = row["event_id"].strip()

        def issue(field, severity, code, message, event_id=event_id, row_number=row_number):
            add_issue(
                issues,
                event_id=event_id,
                row_number=row_number,
                field=field,
                severity=severity,
                code=code,
                message=message,
            )

        if (normalize_name(row["kelurahan"]), normalize_name(row["kecamatan"])) != (area, district):
            dropped += 1
            issue(
                "kelurahan", "INFO", "dropped_other_area", "Row belongs to a different study area"
            )
            continue
        try:
            event_date = parse_date(row["event_date"].strip())
        except ValueError:
            issue("event_date", "ERROR", "bad_date", "Expected a valid ISO date YYYY-MM-DD")
            continue
        confidence = row["location_confidence"].strip().upper()
        if confidence not in confidence_values:
            issue(
                "location_confidence", "ERROR", "invalid_confidence", "Unknown location confidence"
            )
            continue
        source_id = row["source_id"].strip()
        if source_id not in source_ids:
            issue("source_id", "ERROR", "unknown_source", f"Unregistered source: {source_id}")
            continue
        rw_list = parse_rw(row.get("rw_raw"))
        if not rw_list and confidence not in {"KELURAHAN", "UNKNOWN"}:
            issue(
                "location_confidence",
                "WARNING",
                "confidence_mismatch",
                "No RW is stated; use KELURAHAN or UNKNOWN confidence",
            )
        depth_raw = row.get("depth_raw", "")
        depth_min, depth_max = parse_depth(depth_raw)
        if depth_max is None:
            code = "depth_unparsed" if depth_raw.strip() else "depth_missing"
            issue("depth_raw", "INFO", code, "Recorded depth is missing or could not be parsed")
        elif depth_max > 600:
            issue(
                "depth_raw", "WARNING", "depth_implausible", "Depth exceeds 600 cm; verify source"
            )
        for raw_rw in rw_list or [None]:
            rw_no = raw_rw if raw_rw in rw_numbers else None
            if raw_rw is not None and rw_no is None:
                issue(
                    "rw_raw",
                    "WARNING",
                    "rw_not_in_layer",
                    f"RW {raw_rw} is absent from the RW layer",
                )
            events.append(
                Event(
                    event_uid=f"{event_id}#{raw_rw if raw_rw is not None else 'unassigned'}",
                    event_id=event_id,
                    source_id=source_id,
                    source_ref=row["source_ref"].strip(),
                    event_date=event_date,
                    kelurahan=area,
                    kecamatan=district,
                    rw_no=rw_no,
                    location_confidence=confidence,
                    verified=row["verified"].strip().upper(),
                    rt_raw=row.get("rt_raw", ""),
                    address_raw=row.get("address_raw", ""),
                    depth_min_cm=depth_min,
                    depth_max_cm=depth_max,
                    affected_kk=_optional_int(row.get("affected_kk")),
                    affected_people=_optional_int(row.get("affected_people")),
                    row_number=row_number,
                )
            )
        kept += 1
        if len(rw_list) > 1:
            exploded += len(rw_list)
    events = deduplicate(events, source_priority)
    for event in events:
        if event.duplicate_of is not None:
            add_issue(
                issues,
                event_id=event.event_id,
                row_number=event.row_number,
                field="duplicate_of",
                severity="INFO",
                code="duplicate",
                message=f"Cross-source duplicate of {event.duplicate_of}",
            )
    result = ImportResult(
        events,
        issues,
        summarize(
            events,
            issues,
            rows_in=len(rows),
            rows_kept=kept,
            rows_dropped_area=dropped,
            exploded_rows=exploded,
        ),
    )
    if not events:
        raise NoValidRowsError(result)
    return result

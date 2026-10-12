"""Structured, deterministic validation reports and import failure policy."""

from collections import Counter

from .schema import ISSUE_CODES, Event, ImportResult, ValidationIssue


class SchemaError(ValueError):
    """An input table lacks normative required columns."""


class NoValidRowsError(ValueError):
    def __init__(self, result: ImportResult):
        super().__init__("No valid event rows remain; inspect the validation report")
        self.result = result


def require_columns(columns, required):
    missing = sorted(set(required) - set(columns))
    if missing:
        raise SchemaError("Missing required columns: " + ", ".join(missing))


def add_issue(issues, *, event_id="", row_number=0, field="", severity, code, message):
    if code not in ISSUE_CODES:
        raise ValueError(f"Unknown validation issue code: {code}")
    issues.append(
        ValidationIssue(
            f"ISSUE-{len(issues) + 1:06d}",
            event_id,
            row_number,
            field,
            severity,
            code,
            message,
        )
    )


def summarize(
    events: list[Event],
    issues: list[ValidationIssue],
    *,
    rows_in,
    rows_kept,
    rows_dropped_area,
    exploded_rows,
) -> dict:
    levels = Counter(issue.severity for issue in issues)
    return {
        "rows_in": rows_in,
        "rows_kept": rows_kept,
        "rows_dropped_area": rows_dropped_area,
        "exploded_rows": exploded_rows,
        "duplicates": sum(e.duplicate_of is not None for e in events),
        "rw_unassigned": sum(e.rw_no is None for e in events),
        "depth_missing": sum(e.depth_max_cm is None for e in events),
        "years_covered": sorted({e.year for e in events}),
        "errors": levels["ERROR"],
        "warnings": levels["WARNING"],
    }

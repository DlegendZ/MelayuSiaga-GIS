"""Audit publisher CSV granularity without inventing event dates or spatial RW codes."""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    from ._common import ROOT, read_csv, write_json
except ImportError:
    from _common import ROOT, read_csv, write_json

from km_flood_priority.core.normalize import normalize_name, parse_rw
from km_flood_priority.core.validation import require_columns


def inspect_source(headers, rows, *, kelurahan="KAMPUNG MELAYU", kecamatan="JATINEGARA"):
    require_columns(headers, ("kelurahan", "kecamatan"))
    target = normalize_name(kelurahan), normalize_name(kecamatan)
    detail = "tanggal_kejadian" in headers and "rw" in headers
    targets, counts = [], Counter()
    for row_no, row in enumerate(rows, start=2):
        if (normalize_name(row["kelurahan"]), normalize_name(row["kecamatan"])) != target:
            continue
        issues = []
        raw_date, period = row.get("tanggal_kejadian", ""), row.get("periode_data", "")
        if not raw_date:
            issues.append("no_exact_event_date")
        elif re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", raw_date.strip()):
            try:
                parsed = datetime.strptime(raw_date.strip(), "%d/%m/%Y").date()
            except ValueError:
                issues.append("invalid_source_date")
            else:
                if period != parsed.strftime("%Y%m"):
                    issues.append("period_date_conflict")
        else:
            # A monthly list and RW list do not establish a date/RW cross product.
            issues.append("date_needs_source_transcription")
        raw_rw = row.get("rw", "")
        if "rw" not in headers:
            issues.append("no_rw_codes")
        elif not parse_rw(raw_rw) or any(number <= 0 for number in parse_rw(raw_rw)):
            issues.append("rw_unassigned")
        counts.update(issues)
        targets.append(
            {
                "source_ref": f"row {row_no}",
                "periode_data": period,
                "source_date_text": raw_date,
                "rw_raw": raw_rw,
                "issues": issues,
                "human_verified": False,
            }
        )
    return {
        "headers": list(headers),
        "rows_total": len(rows),
        "target_rows_count": len(targets),
        "periods_in_file": sorted({row.get("periode_data", "") for row in rows}),
        "usage": "context_only"
        if not detail
        else "source_review_required"
        if counts or not targets
        else "canonical_conversion_candidate",
        "issue_counts": dict(counts),
        "target_rows": targets,
        "notes": "Publisher periods are not accepted event-year coverage. Counts of affected RW "
        "are not RW codes. Monthly depth ranges are not event-specific measurements. "
        "This audit does not produce canonical events or verify any source row.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, default=ROOT / "data/interim/satudata_audit.json")
    args = parser.parse_args(argv)
    reports = []
    for path in args.inputs:
        headers, rows = read_csv(path)
        report = inspect_source(headers, rows)
        metadata_path = path.with_suffix(".meta.json")
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        )
        report.update(
            {
                "source_file": str(path.resolve()),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "download_url": metadata.get("url"),
                "retrieved_at": metadata.get("retrieved_at"),
            }
        )
        reports.append(report)
        print(
            f"{path.name}: {report['rows_total']} source rows; "
            f"{report['target_rows_count']} target rows; {report['usage']}; "
            f"issues={report['issue_counts']}"
        )
    write_json(
        args.output,
        {"sources": reports, "accepted_event_years": None, "human_source_review_pending": True},
    )
    print(f"Saved audit: {args.output}; no event dates or RW codes were inferred")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"audit_satudata: {error}")

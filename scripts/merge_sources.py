"""Merge canonical CSVs and run FR-1 validation before publishing events_all.csv."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

try:
    from ._common import ROOT, read_csv, write_csv, write_json
except ImportError:
    from _common import ROOT, read_csv, write_csv, write_json

from km_flood_priority.core.normalize import import_events, parse_rw
from km_flood_priority.core.schema import EVENT_COLUMNS, EVENT_REQUIRED, SOURCE_COLUMNS
from km_flood_priority.core.validation import NoValidRowsError, require_columns


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="*")
    parser.add_argument("--sources", type=Path, default=ROOT / "data/clean/sources.csv")
    parser.add_argument("--rw-geojson", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/events_all.csv")
    args = parser.parse_args(argv)
    paths = sorted(args.inputs or (ROOT / "data/clean").glob("events_*.csv"))
    if not paths:
        parser.error(
            "No real canonical event files found in data/clean; acquire and check sources first"
        )
    source_headers, source_rows = read_csv(args.sources)
    require_columns(source_headers, SOURCE_COLUMNS)
    source_ids = [row["source_id"] for row in source_rows]
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("sources.csv contains duplicate source IDs")
    admin = sorted((ROOT / "data/raw/admin").glob("rw_kampung_melayu_*.geojson"))
    rw_path = args.rw_geojson or (admin[-1] if admin else None)
    if rw_path is None:
        parser.error("Fetch official RW polygons first, or provide --rw-geojson")
    raw_rw = json.loads(rw_path.read_text(encoding="utf-8"))
    numbers = {n for f in raw_rw["features"] for n in parse_rw(str(f["properties"]["wadmrw"]))}
    rows = []
    for path in paths:
        headers, items = read_csv(path)
        require_columns(headers, EVENT_REQUIRED)
        rows.extend({column: item.get(column, "") for column in EVENT_COLUMNS} for item in items)
    failure = None
    try:
        result = import_events(
            rows, columns=EVENT_COLUMNS, rw_numbers=numbers, source_ids=set(source_ids)
        )
    except NoValidRowsError as error:
        result, failure = error.result, error
    write_json(
        args.output.with_suffix(".validation.json"),
        {
            "summary": result.summary,
            "issues": [asdict(issue) for issue in result.issues],
            "inputs": [str(path.resolve()) for path in paths],
            "unverified_records": sum(event.verified != "Y" for event in result.events),
        },
    )
    if failure is not None:
        raise failure
    if result.summary["errors"]:
        raise ValueError(
            "Row errors exist; inspect events_all.validation.json and fix source rows first"
        )
    write_csv(args.output, EVENT_COLUMNS, rows)
    print(
        f"Saved {args.output}; years_covered={result.summary['years_covered']}; "
        f"duplicates={result.summary['duplicates']}"
    )
    if any(event.verified != "Y" for event in result.events):
        print(
            "Human verification remains pending; "
            "these inputs do not yet qualify for Phase 4 findings."
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"merge_sources: {error}")

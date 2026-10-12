"""Convert a downloaded Satu Data CSV using an explicitly inspected per-year mapping."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from ._common import ROOT, read_csv, write_csv, write_json
except ImportError:
    from _common import ROOT, read_csv, write_csv, write_json

from km_flood_priority.core.normalize import normalize_name
from km_flood_priority.core.schema import EVENT_COLUMNS

# Populate only after inspecting an actual downloaded year's headers, never from guessed names.
YEAR_COLUMN_MAPPINGS: dict[int, dict] = {}
REQUIRED_MAPPED_FIELDS = {"event_date", "kota", "kecamatan", "kelurahan", "rw_raw"}


def convert(
    headers, rows, mapping, *, year, source_id, kelurahan="KAMPUNG MELAYU", kecamatan="JATINEGARA"
):
    column_map = mapping["column_map"]
    if set(column_map) - set(EVENT_COLUMNS):
        raise ValueError("Mapping contains unknown canonical event fields")
    if REQUIRED_MAPPED_FIELDS - set(column_map):
        raise ValueError("Mapping must explicitly identify date, city, district, kelurahan and RW")
    missing = set(column_map.values()) - set(headers)
    unknown = set(headers) - set(column_map.values()) - set(mapping.get("ignored_columns", []))
    if missing or unknown:
        raise ValueError(
            f"Unrecognized CSV schema: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    output = []
    dropped = 0
    for index, source in enumerate(rows, start=2):
        row = dict.fromkeys(EVENT_COLUMNS, "")
        row.update({target: source[origin].strip() for target, origin in column_map.items()})
        if (normalize_name(row["kelurahan"]), normalize_name(row["kecamatan"])) != (
            normalize_name(kelurahan),
            normalize_name(kecamatan),
        ):
            dropped += 1
            continue
        try:
            when = datetime.strptime(
                row["event_date"], mapping.get("date_format", "%Y-%m-%d")
            ).date()
        except ValueError as error:
            raise ValueError(
                f"Source row {index}: invalid event date {row['event_date']!r}"
            ) from error
        if when.year != year:
            raise ValueError(
                f"Source row {index}: date year {when.year} differs from --year {year}"
            )
        row["event_date"] = when.isoformat()
        row["event_id"] = row["event_id"] or f"SDJ{year}-{index:06d}"
        row["source_id"], row["source_ref"] = source_id, f"row {index}"
        row["location_confidence"], row["verified"] = "RW", "N"
        row["notes"] = "Imported from publisher CSV; human verification pending"
        output.append(row)
    return output, dropped


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument(
        "--mapping", type=Path, help="Inspected mapping JSON; no guessing of columns"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    mapping = (
        json.loads(args.mapping.read_text(encoding="utf-8"))
        if args.mapping
        else (YEAR_COLUMN_MAPPINGS.get(args.year))
    )
    headers, rows = read_csv(args.input)
    if mapping is None:
        parser.error(
            f"No inspected mapping for {args.year}; actual columns: {headers}. Supply --mapping."
        )
    result, dropped = convert(headers, rows, mapping, year=args.year, source_id=args.source_id)
    if not result:
        raise ValueError("No Kampung Melayu / Jatinegara rows remain; record the coverage gap")
    output = args.output or ROOT / f"data/clean/events_satudata_{args.year}.csv"
    write_csv(output, EVENT_COLUMNS, result)
    write_json(
        output.with_suffix(".mapping.json"),
        {
            "source_file": str(args.input.resolve()),
            "mapping": mapping,
            "rows_in": len(rows),
            "rows_kept": len(result),
            "rows_dropped_area": dropped,
            "verified": "N",
        },
    )
    print(f"Saved {len(result)} rows to {output}; {dropped} other-area rows dropped; verified=N")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"convert_satudata: {error}")

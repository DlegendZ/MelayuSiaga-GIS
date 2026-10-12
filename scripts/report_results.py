"""Read-only sanity, sensitivity and Genangan robustness report from real results."""

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from datetime import date
from pathlib import Path
from urllib.parse import quote

try:
    from ._common import ROOT, write_json
except ImportError:
    from _common import ROOT, write_json

from km_flood_priority.core.priority import compute_priority
from km_flood_priority.core.schema import AccessRecord, Event, PriorityParameters, PriorityRecord


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/processed/results.gpkg")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--review-status",
        default="Pending human review; recorded-event priority, not hazard or safety",
        help="Explicit review receipt for this result; new reports default to pending",
    )
    args = parser.parse_args(argv)
    uri = "file:" + quote(args.input.resolve().as_posix(), safe="/:") + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        priority = [
            {name: row[name] for name in PriorityRecord.__dataclass_fields__}
            for row in connection.execute("SELECT * FROM rw_priority ORDER BY rw_no")
        ]
        events = []
        genangan_ids = set()
        for row in connection.execute("SELECT * FROM events ORDER BY fid"):
            values = {name: row[name] for name in Event.__dataclass_fields__ if name in row.keys()}
            values["event_date"] = date.fromisoformat(values["event_date"])
            events.append(Event(**values))
            if "source type Genangan" in (row["notes"] or ""):
                genangan_ids.add((row["source_id"], row["event_id"]))
        access = [
            AccessRecord(**{name: row[name] for name in AccessRecord.__dataclass_fields__})
            for row in connection.execute("SELECT * FROM access_by_rw ORDER BY fid")
        ]
        run = dict(connection.execute("SELECT * FROM run_info").fetchone())
        baseline = {row["rw_no"]: row["priority_class"] for row in priority}
        settings = json.loads(run["parameters_json"])
        rules = PriorityParameters(
            episode_gap_days=settings["EPISODE_GAP_DAYS"],
            rec_med=settings["REC_MED"],
            rec_high=settings["REC_HIGH"],
            depth_high_cm=settings["DEPTH_HIGH_CM"],
        )
        without_genangan = compute_priority(
            [e for e in events if (e.source_id, e.event_id) not in genangan_ids],
            baseline,
            access=access,
            parameters=rules,
        )
        robustness = {
            "excluded_source_records": len(genangan_ids),
            "excluded_normalized_rows": sum(
                (e.source_id, e.event_id) in genangan_ids for e in events
            ),
            "priority": [
                {
                    "rw_no": row.rw_no,
                    "n_records": row.n_records,
                    "n_episodes": row.n_episodes,
                    "priority_class": row.priority_class,
                }
                for row in without_genangan.polygons
            ],
            "changed_rw": [
                row.rw_no
                for row in without_genangan.polygons
                if row.priority_class != baseline[row.rw_no]
            ],
        }
        sensitivity = []
        for recurrence in (2, 3, 4):
            for depth in (30, 50, 80):
                rules = PriorityParameters(
                    episode_gap_days=settings["EPISODE_GAP_DAYS"],
                    rec_med=settings["REC_MED"],
                    rec_high=recurrence,
                    depth_high_cm=depth,
                )
                result = compute_priority(events, baseline, access=access, parameters=rules)
                sensitivity.append(
                    {
                        "REC_HIGH": recurrence,
                        "DEPTH_HIGH_CM": depth,
                        "changed_rw": [
                            row.rw_no
                            for row in result.polygons
                            if row.priority_class != baseline[row.rw_no]
                        ],
                        "class_counts": dict(
                            Counter(row.priority_class for row in result.polygons)
                        ),
                    }
                )
        issue_counts = [
            dict(row)
            for row in connection.execute(
                "SELECT severity,code,count(*) AS n FROM validation_issues GROUP BY severity,code"
            )
        ]
        verified_targets = connection.execute(
            "SELECT count(*) FROM safe_points WHERE verified='Y'"
        ).fetchone()[0]
        notes = [
            dict(row)
            for row in connection.execute(
                "SELECT DISTINCT event_id,notes FROM events "
                "WHERE notes LIKE '%Source inconsistency%'"
            )
        ]
    report = {
        "source_file": str(args.input.resolve()),
        "sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "run_info": run,
        "priority": priority,
        "class_counts": dict(Counter(row["priority_class"] for row in priority)),
        "normalized_rows": len(events),
        "source_records": len({(event.source_id, event.event_id) for event in events}),
        "depth_missing_rows": sum(event.depth_max_cm is None for event in events),
        "rw_unassigned_rows": sum(event.rw_no is None for event in events),
        "access_rows": len(access),
        "access_counts": dict(Counter(row.access_status for row in access)),
        "verified_targets": verified_targets,
        "source_inconsistencies": notes,
        "validation_issue_counts": issue_counts,
        "sensitivity": sensitivity,
        "without_genangan": robustness,
        "result_review": args.review_status,
    }
    output = args.output or args.input.with_suffix(".sanity.json")
    write_json(output, report)
    print(
        json.dumps(
            {
                "report": str(output),
                "class_counts": report["class_counts"],
                "access_counts": report["access_counts"],
                "changed_rw_by_scenario": [row["changed_rw"] for row in sensitivity],
                "without_genangan": robustness,
                "result_review": report["result_review"],
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        sys.exit(f"report_results: {error}")

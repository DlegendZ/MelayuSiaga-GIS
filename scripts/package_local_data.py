"""Package three processed inputs locally; not approved for commit or public release."""

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from ._common import ROOT, read_csv
except ImportError:
    from _common import ROOT, read_csv

from km_flood_priority.core.schema import EVENT_REQUIRED, SOURCE_COLUMNS
from km_flood_priority.core.validation import require_columns


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT / "data/processed/inputs.gpkg")
    parser.add_argument("--events", type=Path, default=ROOT / "data/processed/events_all.csv")
    parser.add_argument("--sources", type=Path, default=ROOT / "data/clean/sources.csv")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "dist/km_flood_priority-local-data.zip"
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output.exists() and not args.overwrite:
        parser.error("Local bundle exists; select another --output or explicitly use --overwrite")
    for path, columns in ((args.events, EVENT_REQUIRED), (args.sources, SOURCE_COLUMNS)):
        headers, rows = read_csv(path)
        require_columns(headers, columns)
        if not rows:
            raise ValueError(f"Empty input table: {path}")
    files = {
        "inputs.gpkg": args.inputs,
        "events_all.csv": args.events,
        "sources.csv": args.sources,
    }
    payloads = {name: path.read_bytes() for name, path in files.items()}
    if not payloads["inputs.gpkg"].startswith(b"SQLite format 3\x00"):
        raise ValueError("inputs.gpkg is not a SQLite/GeoPackage file")
    manifest = {
        "purpose": "Local lecturer attachment only if the lecturer authorizes it",
        "public_distribution_approved": False,
        "decision": "Raynald 2026-10-13: public plugin ZIP excludes sample_data",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "attribution": "DKI indicative boundaries; PPID Jakarta Timur; "
        "© OpenStreetMap contributors / ODbL. See docs/DATA_SOURCES.md.",
        "files": {
            name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in payloads.items()
        },
    }
    payloads["manifest.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    payloads["README.txt"] = (
        "LOCAL ONLY — do not commit, publish or release this archive.\n"
        "DKI boundary and PPID redistribution permission is unresolved.\n"
        "Attach to the lecturer only if the lecturer authorizes the attachment.\n\n"
        "Extract into one folder. In QGIS, add all five layers from inputs.gpkg.\n"
        "Select events_all.csv and sources.csv in Run full pipeline.\n"
        "Keep verified-only targets; the current 440 candidates remain unverified.\n"
        "Recorded event coverage: 2025. Access remains UNKNOWN.\n"
        "Compare extracted files with manifest.json SHA-256 values.\n"
    ).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in payloads.items():
            archive.writestr(name, raw)
    with zipfile.ZipFile(args.output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Local bundle failed ZIP integrity checking")
        for name, raw in payloads.items():
            if archive.read(name) != raw:
                raise ValueError(f"Local bundle failed exact-byte check: {name}")
    print(f"Built LOCAL-ONLY {args.output}; {args.output.stat().st_size} bytes; never release")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        sys.exit(f"package_local_data: {error}")

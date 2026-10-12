"""Shared filesystem, CSV, provenance, and network helpers for development scripts."""

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader, [])
        # Some publisher exports prepend two UTF-8 BOMs; utf-8-sig consumes only one.
        if headers:
            headers[0] = headers[0].lstrip("\ufeff")
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path}: duplicate CSV column names")
        rows = []
        for values in reader:
            if not values or values[0].lstrip().startswith("#"):
                continue
            if len(values) != len(headers):
                raise ValueError(f"{path}, line {reader.line_num}: wrong number of CSV values")
            rows.append(dict(zip(headers, values, strict=True)))
    return headers, rows


def write_csv(path, columns, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Drafts and converted files may later be checked by humans. Never replace them silently.
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def get_json(url, parameters=None, *, payload=None, timeout=45):
    if parameters:
        url += "?" + urlencode(parameters)
    request = Request(
        url,
        data=payload,
        headers={
            "User-Agent": "MelayuSiaga-GIS/1.0 (academic data acquisition)",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
    result = json.loads(raw)
    if "error" in result:
        raise ValueError(f"{url}: server error {result['error']}")
    return result, raw, url


def save_snapshot(path, raw, *, url, query=None, **metadata):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(
            f"Snapshot exists: {path}. Choose another --date; raw data is immutable."
        )
    path.write_bytes(raw)
    info = {
        "url": url,
        "query": query,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        **metadata,
    }
    path.with_suffix(".meta.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

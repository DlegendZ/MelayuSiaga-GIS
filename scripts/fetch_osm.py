"""Fetch OSM roads/buildings and unverified candidates for a QGIS-derived buffered bbox."""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

try:
    from ._common import ROOT, get_json, save_snapshot, write_csv, write_json
except ImportError:
    from _common import ROOT, get_json, save_snapshot, write_csv, write_json

from km_flood_priority.core.schema import SAFE_POINT_COLUMNS

ENDPOINT = "https://overpass-api.de/api/interpreter"


def overpass_query(bbox):
    south, west, north, east = bbox
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise ValueError("Expected bbox south,west,north,east in EPSG:4326")
    box = ",".join(str(value) for value in bbox)
    return (
        f'[out:json][timeout:120];(way["highway"]({box});way["building"]({box});'
        f'nwr["amenity"~"^(school|place_of_worship|community_centre|townhall)$"]({box});'
        f'nwr["office"="government"]({box}););out geom;'
    )


def convert_elements(elements, source_id):
    roads, buildings, candidates = [], [], []
    seen = set()
    for element in elements:
        uid = f"{element['type']}/{element['id']}"
        if uid in seen:
            continue
        seen.add(uid)
        tags = element.get("tags", {})
        coords = [[p["lon"], p["lat"]] for p in element.get("geometry", [])]
        props = {"osm_id": str(element["id"]), **tags}
        if element["type"] == "way" and len(coords) >= 2 and "highway" in tags:
            roads.append(
                {
                    "type": "Feature",
                    "properties": props,
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )
        if (
            element["type"] == "way"
            and len(coords) >= 4
            and coords[0] == coords[-1]
            and "building" in tags
        ):
            buildings.append(
                {
                    "type": "Feature",
                    "properties": props,
                    "geometry": {"type": "Polygon", "coordinates": [coords]},
                }
            )
        candidate_type = tags.get("amenity")
        if candidate_type not in {"school", "place_of_worship", "community_centre", "townhall"}:
            candidate_type = "government" if tags.get("office") == "government" else None
        if candidate_type is None:
            continue
        if "lon" in element and "lat" in element:
            lon, lat = element["lon"], element["lat"]
            note = "OSM node; candidate only; not human verified"
        elif coords:
            vertices = coords[:-1] if coords[0] == coords[-1] else coords
            lon = sum(p[0] for p in vertices) / len(vertices)
            lat = sum(p[1] for p in vertices) / len(vertices)
            note = "Mean of OSM way vertices; candidate only; position/site suitability unverified"
        else:
            continue  # Relations without a representative coordinate require manual inspection.
        candidates.append(
            dict(
                zip(
                    SAFE_POINT_COLUMNS,
                    [
                        f"OSM-{uid}",
                        tags.get("name", uid),
                        candidate_type,
                        "",
                        lon,
                        lat,
                        "N",
                        source_id,
                        f"https://www.openstreetmap.org/{uid}",
                        note,
                    ],
                    strict=True,
                )
            )
        )
    return roads, buildings, candidates


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bbox", help="south,west,north,east; use the 1000 m metric-buffer bbox")
    parser.add_argument("--bbox-file", type=Path, default=ROOT / "data/interim/network_bbox.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/raw/osm")
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument(
        "--date", default=datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d")
    )
    args = parser.parse_args(argv)
    if args.bbox:
        bbox = [float(v) for v in args.bbox.split(",")]
    else:
        if not args.bbox_file.exists():
            parser.error("Run build_inputs.py --prepare-bbox-only with QGIS Python first")
        bbox = json.loads(args.bbox_file.read_text(encoding="utf-8"))["bbox_4326"]
    if len(bbox) != 4:
        parser.error("--bbox requires four numbers")
    query = overpass_query(bbox)
    data, raw, url = get_json(
        args.endpoint, payload=urlencode({"data": query}).encode(), timeout=150
    )
    if data.get("remark"):
        raise ValueError(f"Overpass incomplete response: {data['remark']}")
    roads, buildings, candidates = convert_elements(data.get("elements", []), f"OSM-{args.date}")
    if not roads:
        raise ValueError("Overpass returned no usable roads")
    save_snapshot(
        args.output_dir / f"osm_{args.date}.json",
        raw,
        url=url,
        query=query,
        bbox_4326=bbox,
        attribution="© OpenStreetMap contributors, ODbL",
        element_count=len(data.get("elements", [])),
    )
    for name, features in (("roads", roads), ("buildings", buildings)):
        write_json(
            args.output_dir / f"{name}_{args.date}.geojson",
            {
                "type": "FeatureCollection",
                "features": features,
            },
        )
    write_csv(ROOT / "data/interim/safe_point_candidates_osm.csv", SAFE_POINT_COLUMNS, candidates)
    print(
        f"Saved {len(roads)} roads, {len(buildings)} buildings, "
        f"{len(candidates)} unverified candidates"
    )
    print(
        "Register OSM source metadata. Candidate sites remain verified=N until humans check them."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        sys.exit(f"fetch_osm: {error}")

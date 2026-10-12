"""Download official DKI RW/kelurahan geometry and immutable provenance snapshots."""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from ._common import ROOT, get_json, save_snapshot
except ImportError:
    from _common import ROOT, get_json, save_snapshot

from km_flood_priority.core.normalize import normalize_name, parse_rw

SERVER = "https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Hosted"
RW_URL = f"{SERVER}/ADMINISTRASI_AR_RW/FeatureServer/18"
KEL_SERVICE = f"{SERVER}/Batas_Administrasi_Kelurahan_DKI_Jakarta/FeatureServer"


def select_area(layer_url, kelurahan="KAMPUNG MELAYU", kecamatan="JATINEGARA"):
    query = {
        "where": "wadmkd LIKE '%MELAYU%'",
        "outFields": "wadmkd,wadmkc",
        "returnDistinctValues": "true",
        "returnGeometry": "false",
        "f": "json",
    }
    names, _, _ = get_json(f"{layer_url}/query", query)
    matches = []
    for feature in names.get("features", []):
        attrs = feature["attributes"]
        print(f"Available area: {attrs.get('wadmkd')} / {attrs.get('wadmkc')}")
        if (normalize_name(attrs.get("wadmkd")), normalize_name(attrs.get("wadmkc"))) == (
            normalize_name(kelurahan),
            normalize_name(kecamatan),
        ):
            matches.append((attrs["wadmkd"], attrs["wadmkc"]))
    if len(matches) != 1:
        raise ValueError(f"{layer_url}: expected one exact study-area name pair, found {matches}")
    area, district = (name.replace("'", "''") for name in matches[0])
    return f"wadmkd='{area}' AND wadmkc='{district}'"


def fetch_layer(layer_url, where):
    query = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "returnZ": "false",
        "outSR": 32748,
        "f": "geojson",
    }
    result, raw, url = get_json(f"{layer_url}/query", query)
    if result.get("exceededTransferLimit"):
        raise ValueError("ArcGIS response was truncated; pagination must be implemented before use")
    if result.get("type") != "FeatureCollection" or not result.get("features"):
        raise ValueError(f"{layer_url}: no GeoJSON features for the study area")
    return result, raw, url, query


def validate_rw(result):
    numbers = []
    for feature in result["features"]:
        parsed = parse_rw(str(feature["properties"].get("wadmrw", "")))
        if len(parsed) != 1:
            raise ValueError(f"Invalid RW number: {feature['properties'].get('wadmrw')}")
        numbers.extend(parsed)
        if not feature.get("geometry"):
            raise ValueError(f"RW {parsed[0]} has no geometry")
    if len(numbers) != len(set(numbers)):
        raise ValueError("RW numbers are not unique; inspect the official source")
    return sorted(numbers)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/raw/admin")
    parser.add_argument(
        "--date", default=datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d")
    )
    parser.add_argument(
        "--locator-only",
        action="store_true",
        help="Fetch official Jakarta Timur kelurahan polygons for the F1 locator",
    )
    args = parser.parse_args(argv)
    if args.locator_only:
        service, _, _ = get_json(KEL_SERVICE, {"f": "json"})
        candidates = service.get("layers", [])
        if len(candidates) != 1:
            raise ValueError("Kelurahan layer discovery is ambiguous")
        layer_url = f"{KEL_SERVICE}/{candidates[0]['id']}"
        result, raw, url, query = fetch_layer(layer_url, "wadmkk='JAKARTA TIMUR'")
        if any(
            feature["properties"]["wadmkk"] != "JAKARTA TIMUR" for feature in result["features"]
        ):
            raise ValueError("Locator response includes another municipality")
        path = args.output_dir / f"jakarta_timur_kelurahan_{args.date}.geojson"
        save_snapshot(
            path,
            raw,
            url=url,
            query=query,
            feature_count=len(result["features"]),
            purpose="F1 locator; indicative official boundaries",
            crs="EPSG:32748",
        )
        print(f"Saved {len(result['features'])} official locator polygons: {path}")
        return 0
    rw_where = select_area(RW_URL)
    rw, raw, url, query = fetch_layer(RW_URL, rw_where)
    numbers = validate_rw(rw)
    rw_path = args.output_dir / f"rw_kampung_melayu_{args.date}.geojson"
    save_snapshot(
        rw_path,
        raw,
        url=url,
        query=query,
        feature_count=len(rw["features"]),
        rw_numbers=numbers,
        crs="EPSG:32748",
        geometry_validation="Pending makeValid and dissolved-area checks in build_inputs.py",
    )
    service, _, _ = get_json(KEL_SERVICE, {"f": "json"})
    candidates = service.get("layers", [])
    if len(candidates) != 1:
        raise ValueError(
            f"Kelurahan service layer discovery is ambiguous: {json.dumps(candidates)}"
        )
    kel_url = f"{KEL_SERVICE}/{candidates[0]['id']}"
    kel_where = select_area(kel_url)
    kel, raw, url, query = fetch_layer(kel_url, kel_where)
    kel_path = args.output_dir / f"kelurahan_kampung_melayu_{args.date}.geojson"
    save_snapshot(
        kel_path,
        raw,
        url=url,
        query=query,
        feature_count=len(kel["features"]),
        crs="EPSG:32748",
        geometry_validation="Pending build_inputs.py",
    )
    print(f"Saved {len(numbers)} RW: {numbers}; boundary features: {len(kel['features'])}")
    print(
        "Next: run build_inputs.py --prepare-bbox-only using QGIS Python. "
        f"Raw files: {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        sys.exit(f"fetch_admin_boundaries: {error}")

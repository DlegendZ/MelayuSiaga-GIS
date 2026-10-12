"""Run qgis_process in an isolated profile, optionally through offline QGIS Docker."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from ._common import ROOT, write_json
except ImportError:
    from _common import ROOT, write_json

DEFAULT_IMAGE = "qgis/qgis:3.44.15-noble"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT / "data/processed/inputs.gpkg")
    parser.add_argument("--events", type=Path, default=ROOT / "data/processed/events_all.csv")
    parser.add_argument("--sources", type=Path, default=ROOT / "data/clean/sources.csv")
    parser.add_argument("--closures", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/results.gpkg")
    parser.add_argument("--kelurahan", default="KAMPUNG MELAYU")
    parser.add_argument("--kecamatan", default="JATINEGARA")
    parser.add_argument("--episode-gap-days", type=int, default=2)
    parser.add_argument("--rec-high", type=int, default=3)
    parser.add_argument("--rec-med", type=int, default=2)
    parser.add_argument("--depth-high-cm", type=int, default=50)
    parser.add_argument("--use-unverified-safe-points", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--qgis-process", default="qgis_process")
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    args = parser.parse_args(argv)
    for name in ("inputs", "events", "sources"):
        if not getattr(args, name).is_file():
            parser.error(f"Required real input missing: {getattr(args, name)}")
    if args.output.exists() and not args.overwrite:
        parser.error("Output exists; choose another --output or explicitly use --overwrite")
    if args.docker:
        if shutil.which("docker") is None:
            parser.error("Docker CLI unavailable; start Docker Desktop or use QGIS/OSGeo4W shell")

        def mounted(path):
            try:
                return "/repo/" + path.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                parser.error("Docker input/output paths must be within this repository")

        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--mount",
            f"type=bind,source={ROOT},target=/repo",
            "--workdir",
            "/repo",
            "-e",
            "QT_QPA_PLATFORM=offscreen",
            "--entrypoint",
            "python3",
            args.image,
            "scripts/run_pipeline_cli.py",
            "--inputs",
            mounted(args.inputs),
            "--events",
            mounted(args.events),
            "--sources",
            mounted(args.sources),
            "--output",
            mounted(args.output),
            "--kelurahan",
            args.kelurahan,
            "--kecamatan",
            args.kecamatan,
            "--episode-gap-days",
            str(args.episode_gap_days),
            "--rec-high",
            str(args.rec_high),
            "--rec-med",
            str(args.rec_med),
            "--depth-high-cm",
            str(args.depth_high_cm),
        ]
        if args.closures:
            command.extend(["--closures", mounted(args.closures)])
        if args.use_unverified_safe_points:
            command.append("--use-unverified-safe-points")
        if args.overwrite:
            command.append("--overwrite")
        return subprocess.run(command, check=False).returncode
    binary = shutil.which(args.qgis_process)
    if binary is None:
        parser.error("qgis_process unavailable; use --docker or run from QGIS/OSGeo4W shell")
    inputs = {
        "RW_LAYER": f"{args.inputs.resolve()}|layername=rw",
        "RW_FIELD": "wadmrw",
        "ROADS": f"{args.inputs.resolve()}|layername=roads",
        "SAFE_POINTS": f"{args.inputs.resolve()}|layername=safe_points",
        "KELURAHAN_BOUNDARY": f"{args.inputs.resolve()}|layername=kelurahan_boundary",
        "EVENTS_CSV": str(args.events.resolve()),
        "SOURCES_CSV": str(args.sources.resolve()),
        "OUTPUT_GPKG": str(args.output.resolve()),
        "KELURAHAN": args.kelurahan,
        "KECAMATAN": args.kecamatan,
        "EPISODE_GAP_DAYS": args.episode_gap_days,
        "REC_HIGH": args.rec_high,
        "REC_MED": args.rec_med,
        "DEPTH_HIGH_CM": args.depth_high_cm,
        "USE_UNVERIFIED_SAFE_POINTS": args.use_unverified_safe_points,
        "OVERWRITE": args.overwrite,
    }
    if args.closures:
        inputs["CLOSURES_CSV"] = str(args.closures.resolve())
    with tempfile.TemporaryDirectory(prefix="km-flood-qgis-") as temporary:
        environment = {
            **os.environ,
            "QGIS_PLUGINPATH": str(ROOT),
            "QGIS_CUSTOM_CONFIG_PATH": temporary,
            "XDG_CONFIG_HOME": temporary,
            "QT_QPA_PLATFORM": "offscreen",
        }
        enabled = subprocess.run(
            [binary, "plugins", "enable", "km_flood_priority"],
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if enabled.returncode:
            raise ValueError(f"Plugin enable failed: {enabled.stderr or enabled.stdout}")
        result = subprocess.run(
            [binary, "run", "kmflood:run_pipeline", "-"],
            input=json.dumps({"inputs": inputs}),
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode:
            raise ValueError(f"Pipeline failed: {result.stderr or result.stdout}")
    payload = json.loads(result.stdout)
    write_json(args.output.with_suffix(".run.json"), payload)
    summary = payload["results"]["OUTPUT_SUMMARY"]
    elapsed = payload["results"]["ELAPSED_SECONDS"]
    print(
        f"Saved {args.output}; {elapsed:.3f} s; years_covered={summary['years_covered']}; "
        f"validation errors={summary['errors']}; report={args.output.with_suffix('.run.json')}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"run_pipeline_cli: {error}")

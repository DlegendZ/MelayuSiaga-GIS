"""Build a reproducible installable plugin ZIP, excluding tests and unapproved real data."""

import argparse
import configparser
import sys
import zipfile
from pathlib import Path

try:
    from ._common import ROOT
except ImportError:
    from _common import ROOT


def build_archive(output, *, include_sample_data=False, overwrite=False):
    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"Archive exists: {output}; use another --output or --overwrite")
    source = ROOT / "km_flood_priority"
    required = [
        "metadata.txt",
        "__init__.py",
        "plugin.py",
        "provider.py",
        "LICENSE",
        "help/index.html",
        "styles/rw_priority.qml",
    ]
    if any(not (source / name).is_file() for name in required):
        raise ValueError("Plugin implementation or bundled assets are incomplete")
    files = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing a symlink in plugin package: {path}")
        relative = path.relative_to(source)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if relative.parts[0] == "sample_data" and not include_sample_data:
            continue
        files.append((path, f"km_flood_priority/{relative.as_posix()}"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, name in files:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    if output.stat().st_size >= 10 * 1024 * 1024:
        raise ValueError(f"Plugin ZIP exceeds the 10 MB limit: {output}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--include-sample-data",
        action="store_true",
        help="Only after the human redistribution decision; defaults to excluded",
    )
    args = parser.parse_args(argv)
    metadata = configparser.ConfigParser()
    metadata.read(ROOT / "km_flood_priority/metadata.txt", encoding="utf-8")
    output = args.output or ROOT / f"dist/km_flood_priority-{metadata['general']['version']}.zip"
    result = build_archive(
        output, include_sample_data=args.include_sample_data, overwrite=args.overwrite
    )
    print(
        f"Built {result}; {result.stat().st_size} bytes; real sample data "
        f"{'included by explicit option' if args.include_sample_data else 'excluded'}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"package_plugin: {error}")

import ast
from pathlib import Path


def test_core_has_no_qgis_or_qt_imports():
    root = Path(__file__).parents[2] / "km_flood_priority" / "core"
    for file in root.glob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            assert not any(n.startswith(("qgis", "PyQt", "PySide")) for n in names), file

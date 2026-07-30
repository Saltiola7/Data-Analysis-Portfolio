from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"


def test_marimo_app_exists_and_keeps_prefect_out_of_browser_runtime() -> None:
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "marimo" in imports
    assert "prefect" not in imports
    assert "public_sector_opportunity_pipeline.prefect_adapter" not in imports


def test_browser_runtime_dependencies_and_package_root_are_explicit() -> None:
    source = APP_PATH.read_text(encoding="utf-8")
    marimo_config = (PROJECT_ROOT / ".marimo.toml").read_text(encoding="utf-8")

    assert '"marimo==0.23.15"' in source
    assert '"pandas==3.0.5"' in source
    assert 'pythonpath = ["."]' in marimo_config

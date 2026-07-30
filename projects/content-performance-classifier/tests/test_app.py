from __future__ import annotations

import importlib.util
from pathlib import Path


def test_marimo_app_imports_without_training() -> None:
    app_path = Path(__file__).resolve().parents[1] / "src" / "app.py"
    spec = importlib.util.spec_from_file_location("content_classifier_marimo_app", app_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "app")
    assert callable(module.app.run)


def test_marimo_app_declares_exact_browser_dependencies_and_semantic_tables() -> None:
    app_path = Path(__file__).resolve().parents[1] / "src" / "app.py"
    source = app_path.read_text(encoding="utf-8")

    assert source.count("# /// script") == 1
    assert source.count("# ///") == 2
    assert source.count("# requires-python") == 1
    assert '"marimo==0.23.15"' in source
    assert '"numpy==2.5.1"' in source
    assert '"pandas==3.0.5"' in source
    assert '"scikit-learn==1.9.0"' in source
    assert "mo.ui.table" not in source
    assert "<caption" in source

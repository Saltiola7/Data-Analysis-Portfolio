import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"


def test_marimo_app_imports_without_running_pipeline() -> None:
    spec = importlib.util.spec_from_file_location("wellness_marimo_app", APP_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "app")
    assert callable(module.app.run)


def test_browser_runtime_dependencies_and_package_root_are_explicit() -> None:
    source = APP_PATH.read_text(encoding="utf-8")
    marimo_config = (PROJECT_ROOT / ".marimo.toml").read_text(encoding="utf-8")

    assert '"marimo==0.23.15"' in source
    assert '"pandas==3.0.5"' in source
    assert 'pythonpath = ["."]' in marimo_config

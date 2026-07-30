import importlib.util
from pathlib import Path


def test_marimo_app_imports_without_running_pipeline() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    spec = importlib.util.spec_from_file_location("wellness_marimo_app", app_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "app")
    assert callable(module.app.run)

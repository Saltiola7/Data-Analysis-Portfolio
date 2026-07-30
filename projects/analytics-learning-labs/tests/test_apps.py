from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APPS_ROOT = PROJECT_ROOT / "apps"
PACKAGE_ROOT = PROJECT_ROOT / "analytics_learning_labs"
BROWSER_WHEEL_LOCK = PROJECT_ROOT / "browser-wheel-lock.json"
BROWSER_WHEELS_ROOT = PROJECT_ROOT / "browser_wheels"
APP_FILES = (
    "airline_delays.py",
    "synthetic_cohort.py",
    "restaurant_locations.py",
    "streaming_catalog.py",
    "sports_outcomes.py",
)


def _app_source(app_name: str) -> str:
    return (APPS_ROOT / app_name).read_text(encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes(), usedforsecurity=False).hexdigest()


def _markdown_literals(tree: ast.AST) -> list[str]:
    markdown: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "md":
            continue
        if not node.args:
            continue
        value = node.args[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            markdown.append(textwrap.dedent(value.value))
    return markdown


def _seed_labels(tree: ast.AST) -> list[str]:
    labels: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "number":
            continue
        for keyword in node.keywords:
            if (
                keyword.arg == "label"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                labels.append(keyword.value.value)
    return labels


def test_exactly_five_declared_marimo_apps_exist() -> None:
    actual = {path.name for path in APPS_ROOT.glob("*.py") if path.name != "__init__.py"}
    assert actual == set(APP_FILES)


def test_molab_entrypoints_have_immutable_browser_package_dependency() -> None:
    lock = json.loads(BROWSER_WHEEL_LOCK.read_text(encoding="utf-8"))
    source_commit = lock["source_commit"]
    wheel_sha256 = lock["wheel_sha256"]
    filename = lock["filename"]
    wheel = BROWSER_WHEELS_ROOT / filename
    expected_url = (
        "https://raw.githubusercontent.com/Saltiola7/data-portfolio/"
        f"{source_commit}/projects/analytics-learning-labs/browser_wheels/{filename}"
    )
    expected_requirement = f"analytics-learning-labs @ {expected_url}#sha256={wheel_sha256}"

    assert lock["schema_version"] == 1
    assert lock["distribution"] == "analytics-learning-labs"
    assert lock["version"] == "0.1.0"
    assert re.fullmatch(r"[0-9a-f]{40}", source_commit)
    assert re.fullmatch(r"[0-9a-f]{64}", lock["source_tree_sha256"])
    assert re.fullmatch(r"[0-9a-f]{64}", wheel_sha256)
    assert lock["url"] == expected_url
    assert lock["requirement"] == expected_requirement
    assert wheel.is_file()
    assert _sha256(wheel) == wheel_sha256

    for app_name in APP_FILES:
        source = _app_source(app_name)
        tree = ast.parse(source)
        local_imports = {
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert "analytics_learning_labs" in local_imports
        assert source.count(f'#     "{expected_requirement}",') == 1


@pytest.mark.parametrize("app_name", APP_FILES)
def test_marimo_app_imports_without_running_analysis(app_name: str) -> None:
    app_path = APPS_ROOT / app_name
    spec = importlib.util.spec_from_file_location(
        f"analytics_learning_labs_{app_path.stem}",
        app_path,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "app")
    assert callable(module.app.run)


@pytest.mark.parametrize("app_name", APP_FILES)
def test_app_declares_locked_browser_dependencies_and_accessible_controls(
    app_name: str,
) -> None:
    source = _app_source(app_name)
    tree = ast.parse(source)
    markdown = "\n".join(_markdown_literals(tree))
    headings = re.findall(r"(?m)^#\s+\S.*$", markdown)

    assert source.count("# /// script") == 1
    assert source.count("# ///") == 2
    assert source.count("# requires-python") == 1
    assert '"marimo==0.23.15"' in source
    assert '"pandas==3.0.2"' in source
    assert "seed=seed_control.value" in source
    assert "int(seed_control.value)" not in source
    assert "render_fixture_identity(lab_run)" in source
    assert len(headings) == 1
    assert _seed_labels(tree) == ["Seed"]


@pytest.mark.parametrize("app_name", APP_FILES)
def test_app_exposes_required_evidence_and_text_states(app_name: str) -> None:
    source = _app_source(app_name).casefold()

    assert "fixture" in source
    assert "generator_version" in source
    assert "grain" in source
    assert "limitations" in source
    assert "caption" in source
    assert "loading" in source
    assert "validation" in source and "error" in source
    assert "unexpected" in source and "error" in source
    assert "success" in source or "ready" in source


@pytest.mark.parametrize("app_name", APP_FILES)
def test_app_source_has_no_network_or_owner_side_persistence(
    app_name: str,
) -> None:
    tree = ast.parse(_app_source(app_name))
    banned_imports = {
        "boto3",
        "clickhouse_connect",
        "google",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "urllib",
    }
    imported_roots: set[str] = set()
    banned_calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                banned_calls.append("open")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in {
                "to_csv",
                "to_json",
                "to_parquet",
                "write_bytes",
                "write_text",
            }:
                banned_calls.append(node.func.attr)

    assert imported_roots.isdisjoint(banned_imports)
    assert not banned_calls


@pytest.mark.parametrize(
    "source_path",
    sorted(PACKAGE_ROOT.glob("*.py")),
    ids=lambda path: path.name,
)
def test_shared_package_has_no_network_filesystem_or_process_boundary(
    source_path: Path,
) -> None:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    banned_imports = {
        "boto3",
        "clickhouse_connect",
        "google",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    imported_roots: set[str] = set()
    banned_calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                banned_calls.append("open")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in {
                "write_bytes",
                "write_text",
            }:
                banned_calls.append(node.func.attr)

    assert imported_roots.isdisjoint(banned_imports)
    assert not banned_calls

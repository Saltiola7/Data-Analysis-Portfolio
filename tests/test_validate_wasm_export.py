from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from scripts.validate_wasm_export import ExportValidationError, validate_export


def _write_wheel(root: Path, package: str, member: str | None = None) -> None:
    wheels = root / "public" / "wheels"
    wheels.mkdir(parents=True)
    wheel = wheels / f"{package}-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(member or f"{package}/__init__.py", "")


def test_accepts_one_importable_local_package_wheel(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>Safe export</h1>", encoding="utf-8")
    (tmp_path / "runtime.js").write_text(
        "class ModuleNotFoundError extends Error {}",
        encoding="utf-8",
    )
    _write_wheel(tmp_path, "example_package")

    validate_export(tmp_path, "example_package")


@pytest.mark.parametrize(
    ("file_name", "content"),
    [
        ("index.html", "MarimoExceptionRaisedError"),
        ("state.json", "/Users/private/repository"),
        ("worker.py", "Traceback (most recent call last)"),
    ],
)
def test_rejects_embedded_errors_and_private_paths(
    tmp_path: Path,
    file_name: str,
    content: str,
) -> None:
    (tmp_path / "index.html").write_text("<h1>Safe export</h1>", encoding="utf-8")
    (tmp_path / file_name).write_text(content, encoding="utf-8")
    _write_wheel(tmp_path, "example_package")

    with pytest.raises(ExportValidationError):
        validate_export(tmp_path, "example_package")


def test_rejects_malformed_src_layout_wheel(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>Safe export</h1>", encoding="utf-8")
    _write_wheel(
        tmp_path,
        "example_package",
        member="src/example_package/__init__.py",
    )

    with pytest.raises(ExportValidationError, match="malformed src-layout"):
        validate_export(tmp_path, "example_package")


def test_rejects_missing_or_duplicate_package_wheels(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>Safe export</h1>", encoding="utf-8")

    with pytest.raises(ExportValidationError, match="exactly one"):
        validate_export(tmp_path, "example_package")

    _write_wheel(tmp_path, "example_package")
    duplicate = tmp_path / "public" / "wheels" / "duplicate-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(duplicate, "w") as archive:
        archive.writestr("example_package/__init__.py", "")

    with pytest.raises(ExportValidationError, match="exactly one"):
        validate_export(tmp_path, "example_package")

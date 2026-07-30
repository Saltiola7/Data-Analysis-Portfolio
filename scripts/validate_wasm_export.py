"""Fail closed when a Marimo WASM export is incomplete or mispackaged."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

ERROR_MARKERS = (
    "MarimoExceptionRaisedError",
    "CellNotInitializedError",
    "No module named",
    "Traceback (most recent call last)",
)
PRIVATE_PATH_PATTERNS = (
    re.compile(r"/Users/[^/\s\"']+"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s\"']+"),
)
# Bundled Marimo runtime JavaScript defines error classes by name. Scan only
# notebook/output-bearing text, not framework assets, to avoid false positives.
TEXT_SUFFIXES = {".html", ".json", ".py", ".txt"}


class ExportValidationError(RuntimeError):
    """A generated browser artifact violated a release contract."""


def _normalized_package(package: str) -> str:
    normalized = package.strip().replace("-", "_")
    if not normalized or not normalized.isidentifier():
        raise ExportValidationError(f"invalid Python package name: {package!r}")
    return normalized


def validate_export(export_root: Path, package: str) -> None:
    """Validate the executable shell, embedded outputs, and local package wheel."""

    export_root = export_root.resolve()
    package = _normalized_package(package)
    if not (export_root / "index.html").is_file():
        raise ExportValidationError("WASM export is missing index.html")

    for path in sorted(export_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in ERROR_MARKERS:
            if marker in text:
                raise ExportValidationError(
                    f"WASM export contains {marker!r} in {path.relative_to(export_root)}"
                )
        for pattern in PRIVATE_PATH_PATTERNS:
            if pattern.search(text):
                raise ExportValidationError(
                    f"WASM export contains a private local path in {path.relative_to(export_root)}"
                )

    wheels = sorted((export_root / "public" / "wheels").glob("*.whl"))
    matching: list[Path] = []
    for wheel in wheels:
        try:
            with zipfile.ZipFile(wheel) as archive:
                names = set(archive.namelist())
        except zipfile.BadZipFile as exc:
            raise ExportValidationError(f"WASM export contains an invalid wheel: {wheel}") from exc
        if f"{package}/__init__.py" in names:
            matching.append(wheel)
        if any(name.startswith(f"src/{package}/") for name in names):
            raise ExportValidationError(
                f"WASM export contains malformed src-layout wheel: {wheel.name}"
            )

    if len(matching) != 1:
        raise ExportValidationError(
            f"WASM export must contain exactly one importable {package} wheel"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export_root", type=Path)
    parser.add_argument("--package", required=True)
    args = parser.parse_args()
    validate_export(args.export_root, args.package)
    print(f"WASM package validation passed: {args.package}")


if __name__ == "__main__":
    main()

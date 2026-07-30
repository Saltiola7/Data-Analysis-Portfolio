"""Fail closed when a Marimo WASM export is incomplete or mispackaged."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

ERROR_MARKERS = (
    "MarimoExceptionRaisedError",
    "CellNotInitializedError",
    "ModuleNotFoundError",
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


def _validate_dependencies(
    index_text: str,
    expected_dependencies: tuple[str, ...],
) -> None:
    for dependency in expected_dependencies:
        normalized_dependency = dependency.strip()
        dependency_pattern = re.compile(
            rf"(?<![A-Za-z0-9_.+-]){re.escape(normalized_dependency)}"
            r"(?![A-Za-z0-9_.+-])"
        )
        if not normalized_dependency or dependency_pattern.search(index_text) is None:
            raise ExportValidationError(
                f"WASM export is missing requested dependency {normalized_dependency!r}"
            )


def _validate_text(text: str, location: str) -> None:
    for marker in ERROR_MARKERS:
        if marker in text:
            raise ExportValidationError(f"WASM export contains {marker!r} in {location}")
    for pattern in PRIVATE_PATH_PATTERNS:
        if pattern.search(text):
            raise ExportValidationError(f"WASM export contains a private local path in {location}")


def validate_export(
    export_root: Path,
    package: str,
    *,
    expected_dependencies: tuple[str, ...] = (),
) -> None:
    """Validate the executable shell, embedded outputs, and local package wheel."""

    export_root = export_root.resolve()
    package = _normalized_package(package)
    index_path = export_root / "index.html"
    if not index_path.is_file():
        raise ExportValidationError("WASM export is missing index.html")
    index_text = index_path.read_text(encoding="utf-8", errors="replace")
    _validate_dependencies(index_text, expected_dependencies)

    for path in sorted(export_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        _validate_text(text, str(path.relative_to(export_root)))

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
            with zipfile.ZipFile(wheel) as archive:
                for member in sorted(names):
                    if (
                        member.startswith(f"{package}/")
                        and Path(member).suffix.lower() in TEXT_SUFFIXES
                    ):
                        source = archive.read(member).decode("utf-8", errors="replace")
                        _validate_text(source, f"{wheel.name}!/{member}")
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
    parser.add_argument("--dependency", action="append", default=[])
    args = parser.parse_args()
    validate_export(
        args.export_root,
        args.package,
        expected_dependencies=tuple(args.dependency),
    )
    print(f"WASM package validation passed: {args.package}")


if __name__ == "__main__":
    main()

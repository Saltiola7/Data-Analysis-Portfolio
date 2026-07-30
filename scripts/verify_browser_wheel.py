"""Validate the immutable browser wheel used by direct Molab entrypoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PACKAGE = "analytics_learning_labs"
DISTRIBUTION = "analytics-learning-labs"
VERSION = "0.1.0"
WHEEL_FILENAME = f"{PACKAGE}-{VERSION}-py3-none-any.whl"
PROJECT_RELATIVE = Path("projects/analytics-learning-labs")
PACKAGE_RELATIVE = PROJECT_RELATIVE / PACKAGE
LOCK_FILENAME = "browser-wheel-lock.json"
APP_FILENAMES = (
    "airline_delays.py",
    "synthetic_cohort.py",
    "restaurant_locations.py",
    "streaming_catalog.py",
    "sports_outcomes.py",
)
LOCK_FIELDS = {
    "schema_version",
    "distribution",
    "version",
    "filename",
    "source_commit",
    "source_tree_sha256",
    "wheel_sha256",
    "url",
    "requirement",
}
DIST_INFO_MEMBERS = {
    f"{PACKAGE}-{VERSION}.dist-info/METADATA",
    f"{PACKAGE}-{VERSION}.dist-info/RECORD",
    f"{PACKAGE}-{VERSION}.dist-info/WHEEL",
}
PRIVATE_PATTERNS = (
    re.compile(rb"/Users/[^/\s\"']+"),
    re.compile(rb"[A-Za-z]:\\\\Users\\\\[^\\\s\"']+"),
    re.compile(rb"(?:sk|ghp|xox[baprs])-[A-Za-z0-9_-]{12,}"),
)


class BrowserWheelValidationError(RuntimeError):
    """The browser wheel or its immutable dependency contract is invalid."""


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content, usedforsecurity=False).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def source_tree_digest(files: Mapping[str, bytes]) -> str:
    """Hash sorted relative paths and length-delimited content deterministically."""

    digest = hashlib.sha256(usedforsecurity=False)
    for relative_path, content in sorted(files.items()):
        encoded_path = relative_path.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _run_git(repo_root: Path, *args: str) -> bytes:
    git = shutil.which("git")
    if git is None:
        raise BrowserWheelValidationError("git is required to validate source_commit")
    result = subprocess.run(  # noqa: S603
        [git, *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BrowserWheelValidationError(
            f"git {' '.join(args)} failed: {detail or 'unknown error'}"
        )
    return result.stdout


def _read_committed_sources(repo_root: Path, source_commit: str) -> dict[str, bytes]:
    prefix = PACKAGE_RELATIVE.as_posix()
    output = _run_git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        source_commit,
        "--",
        prefix,
    )
    paths = [
        Path(line)
        for line in output.decode("utf-8").splitlines()
        if line and Path(line).suffix == ".py"
    ]
    if not paths:
        raise BrowserWheelValidationError("source_commit contains no package Python files")

    sources: dict[str, bytes] = {}
    for path in paths:
        try:
            relative_path = path.relative_to(PACKAGE_RELATIVE).as_posix()
        except ValueError as exc:
            raise BrowserWheelValidationError(
                f"source_commit returned a path outside the package: {path}"
            ) from exc
        sources[relative_path] = _run_git(
            repo_root,
            "show",
            f"{source_commit}:{path.as_posix()}",
        )
    return sources


def _read_current_sources(project_root: Path) -> dict[str, bytes]:
    package_root = project_root / PACKAGE
    sources = {
        path.relative_to(package_root).as_posix(): path.read_bytes()
        for path in sorted(package_root.rglob("*.py"))
        if path.is_file()
    }
    if not sources:
        raise BrowserWheelValidationError("working tree contains no package Python files")
    return sources


def _load_lock(lock_path: Path) -> dict[str, Any]:
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BrowserWheelValidationError(f"cannot read {lock_path}: {exc}") from exc
    if not isinstance(lock, dict):
        raise BrowserWheelValidationError("browser wheel lock must be a JSON object")
    if set(lock) != LOCK_FIELDS:
        missing = sorted(LOCK_FIELDS - set(lock))
        extra = sorted(set(lock) - LOCK_FIELDS)
        raise BrowserWheelValidationError(
            f"browser wheel lock fields differ: missing={missing}, extra={extra}"
        )
    return lock


def _validate_lock(lock: Mapping[str, Any]) -> tuple[str, str]:
    source_commit = lock["source_commit"]
    wheel_sha256 = lock["wheel_sha256"]
    source_tree_sha256 = lock["source_tree_sha256"]
    if lock["schema_version"] != 1:
        raise BrowserWheelValidationError("unsupported browser wheel lock schema")
    if lock["distribution"] != DISTRIBUTION or lock["version"] != VERSION:
        raise BrowserWheelValidationError("browser wheel distribution or version differs")
    if lock["filename"] != WHEEL_FILENAME:
        raise BrowserWheelValidationError("browser wheel filename differs")
    if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise BrowserWheelValidationError("source_commit must be a full lowercase Git SHA")
    for name, value in (
        ("source_tree_sha256", source_tree_sha256),
        ("wheel_sha256", wheel_sha256),
    ):
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise BrowserWheelValidationError(f"{name} must be lowercase SHA-256")

    expected_url = (
        "https://raw.githubusercontent.com/Saltiola7/data-portfolio/"
        f"{source_commit}/{PROJECT_RELATIVE.as_posix()}/browser_wheels/{WHEEL_FILENAME}"
    )
    expected_requirement = f"{DISTRIBUTION} @ {expected_url}#sha256={wheel_sha256}"
    if lock["url"] != expected_url:
        raise BrowserWheelValidationError("browser wheel URL is not immutable and canonical")
    if lock["requirement"] != expected_requirement:
        raise BrowserWheelValidationError("browser wheel requirement differs from the lock")
    return expected_url, expected_requirement


def _validate_archive(
    wheel_path: Path,
    committed_sources: Mapping[str, bytes],
) -> None:
    expected_package_members = {
        f"{PACKAGE}/{relative_path}" for relative_path in committed_sources
    }
    expected_members = expected_package_members | DIST_INFO_MEMBERS
    try:
        with zipfile.ZipFile(wheel_path) as archive:
            names = set(archive.namelist())
            if names != expected_members:
                raise BrowserWheelValidationError(
                    "browser wheel member set differs from reviewed package and metadata"
                )
            for info in archive.infolist():
                mode = (info.external_attr >> 16) & 0o777
                if mode & 0o111:
                    raise BrowserWheelValidationError(
                        f"browser wheel contains executable member: {info.filename}"
                    )
                content = archive.read(info)
                if any(pattern.search(content) for pattern in PRIVATE_PATTERNS):
                    raise BrowserWheelValidationError(
                        f"browser wheel contains private material: {info.filename}"
                    )
            for relative_path, expected_content in committed_sources.items():
                member = f"{PACKAGE}/{relative_path}"
                if archive.read(member) != expected_content:
                    raise BrowserWheelValidationError(
                        f"browser wheel source differs at {relative_path}"
                    )
            wheel_metadata = archive.read(f"{PACKAGE}-{VERSION}.dist-info/WHEEL").decode("utf-8")
            if "Root-Is-Purelib: true" not in wheel_metadata:
                raise BrowserWheelValidationError("browser wheel is not pure Python")
            if "Tag: py3-none-any" not in wheel_metadata:
                raise BrowserWheelValidationError("browser wheel is not Pyodide-compatible")
    except zipfile.BadZipFile as exc:
        raise BrowserWheelValidationError("browser wheel is not a valid ZIP archive") from exc


def validate_browser_wheel(project_root: Path, repo_root: Path) -> None:
    """Validate lock, artifact, source parity, archive safety, and app headers."""

    project_root = project_root.resolve()
    repo_root = repo_root.resolve()
    lock = _load_lock(project_root / LOCK_FILENAME)
    _, expected_requirement = _validate_lock(lock)
    source_commit = lock["source_commit"]

    _run_git(repo_root, "merge-base", "--is-ancestor", source_commit, "HEAD")
    committed_sources = _read_committed_sources(repo_root, source_commit)
    current_sources = _read_current_sources(project_root)
    if current_sources != committed_sources:
        raise BrowserWheelValidationError(
            "working package source differs from immutable source_commit"
        )
    if source_tree_digest(committed_sources) != lock["source_tree_sha256"]:
        raise BrowserWheelValidationError("source-tree SHA-256 differs from lock")

    wheel_path = project_root / "browser_wheels" / lock["filename"]
    if not wheel_path.is_file():
        raise BrowserWheelValidationError(f"browser wheel is missing: {wheel_path}")
    if _sha256_file(wheel_path) != lock["wheel_sha256"]:
        raise BrowserWheelValidationError("browser wheel SHA-256 differs from lock")
    _validate_archive(wheel_path, committed_sources)

    expected_header_line = f'#     "{expected_requirement}",'
    for app_name in APP_FILENAMES:
        app_path = project_root / "apps" / app_name
        source = app_path.read_text(encoding="utf-8")
        if source.count(expected_header_line) != 1:
            raise BrowserWheelValidationError(
                f"{app_name} does not declare the exact immutable browser wheel"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_RELATIVE,
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    validate_browser_wheel(args.project_root, args.repo_root)
    print("Browser wheel validation passed")


if __name__ == "__main__":
    main()

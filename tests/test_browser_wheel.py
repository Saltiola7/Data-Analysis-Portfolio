from __future__ import annotations

import json
import zipfile
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts.verify_browser_wheel import (
    PACKAGE,
    VERSION,
    BrowserWheelValidationError,
    _validate_archive,
    _validate_lock,
    source_tree_digest,
    validate_browser_wheel,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPO_ROOT / "projects" / "analytics-learning-labs"
WHEEL_PATH = PROJECT_ROOT / "browser_wheels" / "analytics_learning_labs-0.1.0-py3-none-any.whl"


def _package_sources() -> dict[str, bytes]:
    package_root = PROJECT_ROOT / PACKAGE
    return {
        path.relative_to(package_root).as_posix(): path.read_bytes()
        for path in sorted(package_root.rglob("*.py"))
    }


def _rewrite_wheel_member(
    target: Path,
    member: str,
    transform: Callable[[bytes], bytes],
) -> None:
    with (
        zipfile.ZipFile(WHEEL_PATH) as source,
        zipfile.ZipFile(target, mode="w") as destination,
    ):
        for info in source.infolist():
            content = source.read(info)
            if info.filename == member:
                content = transform(content)
            destination.writestr(info, content)


def test_source_tree_digest_binds_paths_and_content() -> None:
    original = {"a.py": b"same", "b.py": b"value"}

    assert source_tree_digest(original) == source_tree_digest(dict(reversed(original.items())))
    assert source_tree_digest(original) != source_tree_digest(
        {"renamed.py": b"same", "b.py": b"value"}
    )
    assert source_tree_digest(original) != source_tree_digest(
        {"a.py": b"same", "b.py": b"changed"}
    )


def test_lock_rejects_mutable_source_url() -> None:
    lock = json.loads((PROJECT_ROOT / "browser-wheel-lock.json").read_text(encoding="utf-8"))
    lock["url"] = lock["url"].replace(lock["source_commit"], "main")

    with pytest.raises(
        BrowserWheelValidationError,
        match="not immutable and canonical",
    ):
        _validate_lock(lock)


def test_committed_browser_wheel_matches_source_and_apps() -> None:
    validate_browser_wheel(PROJECT_ROOT, REPO_ROOT)


def test_browser_wheel_rejects_unlocked_metadata_dependency(tmp_path: Path) -> None:
    metadata_member = f"{PACKAGE}-{VERSION}.dist-info/METADATA"
    changed_wheel = tmp_path / WHEEL_PATH.name

    def add_dependency(content: bytes) -> bytes:
        return content + b"Requires-Dist: unreviewed-package @ https://example.com/pkg.whl\n"

    _rewrite_wheel_member(changed_wheel, metadata_member, add_dependency)

    with pytest.raises(
        BrowserWheelValidationError,
        match="metadata dependencies differ",
    ):
        _validate_archive(changed_wheel, _package_sources())


def test_browser_wheel_rejects_record_hash_drift(tmp_path: Path) -> None:
    record_member = f"{PACKAGE}-{VERSION}.dist-info/RECORD"
    changed_wheel = tmp_path / WHEEL_PATH.name

    def corrupt_first_hash(content: bytes) -> bytes:
        return content.replace(b",sha256=", b",sha256=corrupt", 1)

    _rewrite_wheel_member(changed_wheel, record_member, corrupt_first_hash)

    with pytest.raises(
        BrowserWheelValidationError,
        match="RECORD integrity differs",
    ):
        _validate_archive(changed_wheel, _package_sources())


def test_browser_wheel_rejects_duplicate_archive_members(tmp_path: Path) -> None:
    metadata_member = f"{PACKAGE}-{VERSION}.dist-info/METADATA"
    changed_wheel = tmp_path / WHEEL_PATH.name
    changed_wheel.write_bytes(WHEEL_PATH.read_bytes())
    with zipfile.ZipFile(changed_wheel, mode="a") as archive:
        content = archive.read(metadata_member)
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr(metadata_member, content)

    with pytest.raises(
        BrowserWheelValidationError,
        match="duplicate archive members",
    ):
        _validate_archive(changed_wheel, _package_sources())

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_browser_wheel import (
    BrowserWheelValidationError,
    _validate_lock,
    source_tree_digest,
    validate_browser_wheel,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPO_ROOT / "projects" / "analytics-learning-labs"


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

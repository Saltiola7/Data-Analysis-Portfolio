from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_session_snapshot import (
    SessionValidationError,
    compare_session_sources,
    validate_session,
)


def _write_session(
    path: Path,
    *,
    marker: str = "Expected evidence",
    random_id: str = "random-a",
    code_hash: str = "code-a",
) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "1",
                "metadata": {
                    "marimo_version": "0.23.15",
                    "script_metadata_hash": "script-a",
                },
                "cells": [
                    {
                        "id": "cell-a",
                        "code_hash": code_hash,
                        "outputs": [
                            {
                                "type": "data",
                                "data": {
                                    "text/html": (
                                        f"<h1>{marker}</h1><marimo-ui-element "
                                        f"random-id='{random_id}'></marimo-ui-element>"
                                    )
                                },
                            }
                        ],
                        "console": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_accepts_stable_sources_despite_random_output_ids(tmp_path: Path) -> None:
    committed = tmp_path / "committed.json"
    fresh = tmp_path / "fresh.json"
    _write_session(committed, random_id="random-a")
    _write_session(fresh, random_id="random-b")

    validate_session(committed, ("Expected evidence",))
    validate_session(fresh, ("Expected evidence",))
    compare_session_sources(committed, fresh)


def test_rejects_source_drift(tmp_path: Path) -> None:
    committed = tmp_path / "committed.json"
    fresh = tmp_path / "fresh.json"
    _write_session(committed)
    _write_session(fresh, code_hash="code-b")

    with pytest.raises(SessionValidationError, match="source hashes"):
        compare_session_sources(committed, fresh)


@pytest.mark.parametrize(
    "marker",
    [
        "Traceback (most recent call last)",
        "MarimoExceptionRaisedError",
        "/Users/private/repository",
    ],
)
def test_rejects_errors_and_private_paths(tmp_path: Path, marker: str) -> None:
    session = tmp_path / "session.json"
    _write_session(session, marker=marker)

    with pytest.raises(SessionValidationError):
        validate_session(session, ())


def test_rejects_missing_required_output_marker(tmp_path: Path) -> None:
    session = tmp_path / "session.json"
    _write_session(session)

    with pytest.raises(SessionValidationError, match="required marker"):
        validate_session(session, ("Missing evidence",))

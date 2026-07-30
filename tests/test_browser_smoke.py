from __future__ import annotations

import pytest

from scripts.browser_smoke import _is_allowed_remote_noise, _is_runtime_error


@pytest.mark.parametrize(
    "message",
    [
        '{"type":"exception"}',
        "ModuleNotFoundError: No module named 'analytics_learning_labs'",
        "No module named analytics_learning_labs",
        "Traceback (most recent call last):",
        "MarimoExceptionRaisedError",
        "CellNotInitializedError",
        "Ancestor raised",
    ],
)
def test_runtime_error_classifier_rejects_notebook_failures(message: str) -> None:
    assert _is_runtime_error(message)


@pytest.mark.parametrize(
    "message",
    [
        "debug: loading Pyodide packages",
        "Failed to load resource: relay.vector.co returned 403",
        "visitor ID unavailable for telemetry",
        "export_demos/wasm-intro.py returned 404",
    ],
)
def test_remote_noise_allowlist_is_narrow_and_never_hides_runtime_errors(
    message: str,
) -> None:
    assert _is_allowed_remote_noise(message)
    assert not _is_runtime_error(message)


def test_unknown_console_error_is_not_allowlisted() -> None:
    assert not _is_allowed_remote_noise("Failed to load required application module")

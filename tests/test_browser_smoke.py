from __future__ import annotations

import json

import pytest

from scripts.browser_smoke import (
    _has_live_learning_lab_evidence,
    _is_allowed_remote_noise,
    _is_runtime_error,
    _wellness_seed_input,
)


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
        "Failed to load resource: api.cr-relay.com returned 403",
        "visitor ID unavailable for telemetry",
        "No visitor ID available. Load may have failed.",
        "Load failed, error in settings [https://molab.marimo.io/_next/chunk.js]",
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
    assert not _is_allowed_remote_noise("Load failed, error in settings")


def test_normal_runtime_config_is_not_a_python_traceback() -> None:
    assert not _is_runtime_error('{"runtime": {"show_tracebacks": false}}')


def test_live_learning_lab_gate_rejects_static_source_literals() -> None:
    console_messages = [
        (
            "debug",
            'startSession {"code":"Success: analysis ready. fixture-identity primary-table"}',
        )
    ]

    assert not _has_live_learning_lab_evidence(console_messages)


def _kernel_cell_message(run_id: str | None, output: str) -> tuple[str, str]:
    kernel_message = json.dumps(
        {
            "op": "cell-op",
            "data": {
                "op": "cell-op",
                "output": {"data": output},
                "run_id": run_id,
            },
        }
    )
    console_payload = json.dumps(
        {
            "id": "kernelMessage",
            "payload": {"message": kernel_message},
            "type": "message",
        }
    )
    return (
        "debug",
        f"[rpc] Worker -> Parent {console_payload} [https://marimo.app/runtime.js]",
    )


def test_live_learning_lab_gate_rejects_cached_null_run() -> None:
    console_messages = [
        _kernel_cell_message(None, "Success: analysis ready."),
        _kernel_cell_message(None, "fixture-identity"),
        _kernel_cell_message(None, "primary-table"),
    ]

    assert not _has_live_learning_lab_evidence(console_messages)


def test_live_learning_lab_gate_rejects_markers_from_different_runs() -> None:
    console_messages = [
        _kernel_cell_message("run-1", "Success: analysis ready."),
        _kernel_cell_message("run-2", "fixture-identity"),
        _kernel_cell_message("run-3", "primary-table"),
    ]

    assert not _has_live_learning_lab_evidence(console_messages)


def test_live_learning_lab_gate_requires_one_executed_run() -> None:
    console_messages = [
        _kernel_cell_message("run-live", "Success: analysis ready."),
        _kernel_cell_message("run-live", "fixture-identity"),
        _kernel_cell_message("run-live", "primary-table"),
    ]

    assert _has_live_learning_lab_evidence(console_messages)


def test_wellness_seed_uses_the_single_numeric_input() -> None:
    class NumericInput:
        def count(self) -> int:
            return 1

    class Target:
        def __init__(self) -> None:
            self.selector = ""
            self.numeric_input = NumericInput()

        def locator(self, selector: str) -> NumericInput:
            self.selector = selector
            return self.numeric_input

    target = Target()

    assert _wellness_seed_input(target) is target.numeric_input
    assert target.selector == 'input[inputmode="numeric"]'

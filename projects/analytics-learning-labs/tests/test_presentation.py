from __future__ import annotations

import pandas as pd
import pytest

from analytics_learning_labs.contracts import AnalysisResult
from analytics_learning_labs.presentation import (
    LabRun,
    render_bar_evidence,
    render_fixture_identity,
    run_lab,
)


def _analysis_result(frame: pd.DataFrame) -> AnalysisResult:
    return AnalysisResult(
        lab_slug="example",
        grain="one fictional record",
        metrics={"records": len(frame)},
        primary_table=frame,
        secondary_table=None,
        notes=("Synthetic evidence.",),
    )


def test_run_lab_returns_complete_success_evidence() -> None:
    def generator(*, seed: int) -> pd.DataFrame:
        return pd.DataFrame({"record_id": [f"example-{seed}"]})

    run = run_lab(generator, _analysis_result, seed=7)

    assert run.state == "success"
    assert run.frame is not None
    assert run.result is not None
    assert run.seed == 7
    assert run.message == "Success: analysis ready."


def test_run_lab_fails_closed_on_validation_error() -> None:
    def generator(*, seed: int) -> pd.DataFrame:
        raise ValueError(f"seed {seed} is invalid")

    run = run_lab(generator, _analysis_result, seed=7)

    assert run.state == "validation-error"
    assert run.frame is None
    assert run.result is None
    assert run.seed is None
    assert "seed 7 is invalid" in run.message


def test_run_lab_hides_unexpected_exception_details() -> None:
    private_detail = "/" + "Users/private/project"

    def generator(*, seed: int) -> pd.DataFrame:
        raise RuntimeError(f"{private_detail}; seed={seed}")

    run = run_lab(generator, _analysis_result, seed=7)

    assert run.state == "unexpected-error"
    assert run.frame is None
    assert run.result is None
    assert run.seed is None
    assert run.message == "Unexpected error: analysis could not run safely."
    assert private_detail not in run.message


@pytest.mark.parametrize("seed", [None, True, 1.5, -1, 1_000_000])
def test_run_lab_fails_closed_on_invalid_seed(seed: object) -> None:
    def generator(*, seed: int) -> pd.DataFrame:
        return pd.DataFrame({"record_id": [f"example-{seed}"]})

    run = run_lab(generator, _analysis_result, seed=seed)

    assert run.state == "validation-error"
    assert run.frame is None
    assert run.result is None
    assert run.seed is None
    assert run.message == "Validation error: seed must be an integer from 0 to 999999"


def test_run_lab_normalizes_integral_float_seed() -> None:
    def generator(*, seed: int) -> pd.DataFrame:
        return pd.DataFrame({"record_id": [f"example-{seed}"]})

    run = run_lab(generator, _analysis_result, seed=7.0)

    assert run.state == "success"
    assert run.seed == 7


def test_fixture_identity_exposes_content_hash() -> None:
    frame = pd.DataFrame({"record_id": ["example-1"]})
    frame.attrs["generator_version"] = "generator/1"
    frame.attrs["fixture_sha256"] = "a" * 64
    result = AnalysisResult(
        lab_slug="example",
        grain="one fictional record",
        metrics={"records": 1},
        primary_table=frame,
        secondary_table=None,
        notes=("Synthetic evidence.",),
    )
    run = LabRun(
        frame=frame,
        result=result,
        seed=7,
        state="success",
        message="Success.",
    )

    rendered = render_fixture_identity(run)

    assert "sha256=" + ("a" * 64) in rendered
    assert f"pandas={pd.__version__}" in rendered


def test_bar_evidence_rejects_nonfinite_values() -> None:
    frame = pd.DataFrame({"label": ["invalid"], "value": [float("inf")]})

    with pytest.raises(ValueError, match="finite"):
        render_bar_evidence(
            frame,
            label_column="label",
            value_column="value",
            title="Evidence",
            description="Accessible evidence.",
        )


def test_bar_evidence_inherits_readable_theme_color() -> None:
    frame = pd.DataFrame({"label": ["valid"], "value": [1.0]})

    rendered = render_bar_evidence(
        frame,
        label_column="label",
        value_column="value",
        title="Evidence",
        description="Accessible evidence.",
    )

    assert 'fill="currentColor"' in rendered

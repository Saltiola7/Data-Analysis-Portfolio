import pandas as pd

from wellness_data_pipeline import generate_synthetic_fixture, run_pipeline


def test_synthetic_fixture_is_deterministic_and_versioned() -> None:
    first = generate_synthetic_fixture(seed=2026)
    second = generate_synthetic_fixture(seed=2026)

    assert first.generator_version == "wellness-synthetic-v2"
    assert first.seed == 2026
    pd.testing.assert_frame_equal(first.participants, second.participants)
    pd.testing.assert_frame_equal(first.programs, second.programs)
    pd.testing.assert_frame_equal(first.daily_signals, second.daily_signals)
    pd.testing.assert_frame_equal(first.interventions, second.interventions)


def test_different_seed_changes_generated_values() -> None:
    first = generate_synthetic_fixture(seed=2026)
    second = generate_synthetic_fixture(seed=2027)

    assert not first.daily_signals.equals(second.daily_signals)


def test_fixture_runs_without_private_configuration_or_external_data() -> None:
    fixture = generate_synthetic_fixture()

    result = run_pipeline(
        fixture.participants,
        fixture.programs,
        fixture.daily_signals,
        fixture.interventions,
    )

    assert not result.participant_days.empty
    assert set(result.participant_days["quality_status"]) == {"accepted"}
    assert not result.rejected_records.empty
    assert result.audit["schema_version"] == "1.1"
    assert len(fixture.programs) >= 3
    assert "unknown_program" in set(result.rejected_records["reason_code"])

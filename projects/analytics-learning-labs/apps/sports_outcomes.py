# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#     "marimo==0.23.15",
#     "pandas==3.0.2",
#     "analytics-learning-labs @ https://raw.githubusercontent.com/Saltiola7/data-portfolio/408740d6edbc58aa7309af308b859daa83fabc58/projects/analytics-learning-labs/browser_wheels/analytics_learning_labs-0.1.0-py3-none-any.whl#sha256=786715a87b8aacd198a5945f44909e0c0e19657c9bb1e50256d776ba12685052",
# ]
# ///
"""Interactive fictional judo medal learning lab."""

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")

with app.setup:
    import marimo as mo

    from analytics_learning_labs import (
        analyze_sports_outcomes,
        generate_sports_fixture,
    )
    from analytics_learning_labs.presentation import (
        render_bar_evidence,
        render_captioned_table,
        render_fixture_identity,
        render_metric_cards,
        run_lab,
    )


@app.cell
def _():
    mo.md("""
    # Judo Medal Explorer

    Compare fictional medal rates while preserving one athlete-event grain. Fixture identity displays `generator_version`, seed, row count, grain, and canonical CSV SHA-256.

    **Status semantics:** Loading means recomputation is pending. Success means evidence is ready. Validation error and unexpected error states fail closed without showing a partial result.

    **Limitations:** Athlete IDs, teams, events, and medal outcomes are synthetic. Descriptive rates do not measure real athlete ability, national performance, competitive strength, or causal effects.
    """)
    return


@app.cell
def _():
    seed_control = mo.ui.number(
        start=0,
        stop=999_999,
        step=1,
        value=2026,
        label="Seed",
    )
    return (seed_control,)


@app.cell
def _(seed_control):
    mo.vstack([mo.md("## Controls"), seed_control])
    return


@app.cell
def _(seed_control):
    lab_run = run_lab(
        generate_sports_fixture,
        analyze_sports_outcomes,
        seed=seed_control.value,
    )
    return (lab_run,)


@app.cell
def _(lab_run):
    _kind = {
        "success": "success",
        "validation-error": "warn",
        "unexpected-error": "danger",
    }[lab_run.state]
    mo.callout(lab_run.message, kind=_kind)
    return


@app.cell
def _(lab_run):
    mo.Html(render_fixture_identity(lab_run))
    return


@app.cell
def _(lab_run):
    _metrics = (
        mo.Html(render_metric_cards(lab_run.result.metrics))
        if lab_run.result is not None
        else mo.md("*Metrics unavailable because validation failed.*")
    )
    _metrics
    return


@app.cell
def _(lab_run):
    _table = (
        mo.Html(
            render_captioned_table(
                lab_run.result.primary_table,
                caption=f"Team medal-rate evidence for seed {lab_run.seed}",
                test_id="primary-table",
            )
        )
        if lab_run.result is not None
        else mo.md("*Primary table unavailable because validation failed.*")
    )
    _table
    return


@app.cell
def _(lab_run):
    _chart = (
        mo.Html(
            render_bar_evidence(
                lab_run.result.primary_table,
                label_column="team",
                value_column="medal_rate_percent",
                title="Medal rate by fictional team",
                description=(
                    "Horizontal bars show fictional medals divided by athlete-events "
                    "for each team."
                ),
            )
        )
        if lab_run.result is not None
        else mo.md("*Visual evidence unavailable because validation failed.*")
    )
    _chart
    return


@app.cell
def _(lab_run):
    _secondary = (
        mo.Html(
            render_captioned_table(
                lab_run.result.secondary_table,
                caption=f"Weight-class evidence for seed {lab_run.seed}",
                test_id="secondary-table",
            )
        )
        if lab_run.result is not None and lab_run.result.secondary_table is not None
        else mo.md("*Secondary table unavailable.*")
    )
    _secondary
    return


@app.cell
def _(lab_run):
    _notes = (
        " ".join(lab_run.result.notes)
        if lab_run.result is not None
        else "No conclusions are available from an invalid fixture."
    )
    mo.callout(f"Interpretation boundary: {_notes}", kind="info")
    return


if __name__ == "__main__":
    app.run()

# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#     "marimo==0.23.15",
#     "pandas==3.0.2",
# ]
# ///
"""Interactive restaurant location-quality learning lab with synthetic data."""

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")

with app.setup:
    import marimo as mo

    from analytics_learning_labs import (
        analyze_restaurant_locations,
        generate_restaurant_fixture,
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
    # Restaurant Location Quality Lab

    Validate fictional geographic coordinates and preserve every bounded missing-coordinate example in an explicit unresolved ledger. Fixture identity displays `generator_version`, seed, row count, one-location grain, and canonical CSV SHA-256.

    **Status semantics:** Loading means recomputation is pending. Success means evidence is ready. Validation error and unexpected error states fail closed without showing a partial result.

    **Limitations:** Labels, countries, regions, and coordinates are synthetic. This lab demonstrates location-data quality control, not market demand, restaurant performance, or expansion suitability.
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
        generate_restaurant_fixture,
        analyze_restaurant_locations,
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
                caption=f"Accepted fictional locations for seed {lab_run.seed}",
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
    if lab_run.result is None:
        _chart = mo.md("*Visual evidence unavailable because validation failed.*")
    else:
        _region_counts = (
            lab_run.result.primary_table.groupby("region", as_index=False, observed=True)
            .agg(accepted_locations=("record_id", "count"))
            .sort_values(["accepted_locations", "region"], ascending=[False, True])
        )
        _chart = mo.Html(
            render_bar_evidence(
                _region_counts,
                label_column="region",
                value_column="accepted_locations",
                title="Accepted fictional locations by region",
                description=(
                    "Horizontal bars count accepted coordinate records in each fictional region."
                ),
            )
        )
    _chart
    return


@app.cell
def _(lab_run):
    _secondary = (
        mo.Html(
            render_captioned_table(
                lab_run.result.secondary_table,
                caption=f"Unresolved coordinate ledger for seed {lab_run.seed}",
                test_id="secondary-table",
            )
        )
        if lab_run.result is not None and lab_run.result.secondary_table is not None
        else mo.md("*Unresolved ledger unavailable.*")
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

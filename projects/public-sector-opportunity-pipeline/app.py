# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#     "marimo==0.23.15",
#     "pandas==3.0.5",
# ]
# ///
"""Interactive evidence explorer for the synthetic opportunity pipeline."""

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")

with app.setup:
    import html as _html

    import marimo as mo

    from public_sector_opportunity_pipeline import (
        FitPreferences,
        dataframe_to_safe_csv,
        generate_synthetic_sources,
        manifest_to_json,
        run_pipeline,
        score_opportunities,
    )

    def render_table(frame, caption, *, row_limit=200):
        rows = frame.head(row_limit).to_dict(orient="records")
        if not rows:
            return mo.md("*No rows are available.*")

        def _cell(value):
            rendered = "" if value is None else str(value)
            return _html.escape(rendered).replace("\n", "<br>")

        header = "".join(
            f'<th scope="col" style="text-align:left;padding:0.5rem;'
            f'border-bottom:1px solid var(--sl-color-neutral-300)">{_cell(column)}</th>'
            for column in frame.columns
        )
        body = "".join(
            "<tr>"
            + "".join(
                f'<td style="vertical-align:top;padding:0.5rem;'
                f'border-bottom:1px solid var(--sl-color-neutral-200)">'
                f"{_cell(row.get(column, ''))}</td>"
                for column in frame.columns
            )
            + "</tr>"
            for row in rows
        )
        limit_note = (
            f'<p style="margin-top:0.5rem">Showing first {row_limit} rows.</p>'
            if len(frame) > row_limit
            else ""
        )
        return mo.Html(
            f'<div style="max-width:100%;overflow:auto;max-height:34rem">'
            f'<table style="width:100%;border-collapse:collapse">'
            f'<caption style="text-align:left;font-weight:600;padding:0.5rem 0">'
            f"{_cell(caption)}</caption><thead><tr>{header}</tr></thead>"
            f"<tbody>{body}</tbody></table>{limit_note}</div>"
        )


@app.cell
def _():
    mo.md("""
    # Public-sector Opportunity Pipeline

    Explore a deterministic, incremental two-source pipeline built from fictional
    records. Every row is normalized, validated, versioned, merged, scored with
    visible rules, and represented in a content-hashed run manifest.

    No live procurement endpoint, contact data, credential, or employer system is
    used. Scores are additive screening rules, not suitability probabilities.
    """)


@app.cell
def _():
    seed_input = mo.ui.number(
        start=0,
        stop=999_999,
        step=1,
        value=2026,
        label="Synthetic fixture seed",
    )
    skill_input = mo.ui.multiselect(
        options=[
            "ai",
            "analytics",
            "data-engineering",
            "gcp",
            "observability",
            "python",
            "search",
            "sql",
        ],
        value=["python", "gcp"],
        label="Preferred skills",
    )
    engagement_input = mo.ui.multiselect(
        options=["contract", "project", "consulting"],
        value=["contract", "project"],
        label="Preferred engagement types",
    )
    remote_input = mo.ui.switch(
        value=True,
        label="Prefer remote or flexible work",
    )
    minimum_value_input = mo.ui.number(
        start=0,
        stop=1_000_000,
        step=10_000,
        value=100_000,
        label="Minimum opportunity ceiling (USD)",
    )
    return (
        engagement_input,
        minimum_value_input,
        remote_input,
        seed_input,
        skill_input,
    )


@app.cell
def _(
    engagement_input,
    minimum_value_input,
    remote_input,
    seed_input,
    skill_input,
):
    mo.vstack(
        [
            mo.md("## Reproducible inputs"),
            mo.hstack(
                [seed_input, minimum_value_input, remote_input],
                justify="start",
            ),
            mo.hstack([skill_input, engagement_input], justify="start"),
        ]
    )


@app.cell
def _(
    engagement_input,
    minimum_value_input,
    remote_input,
    seed_input,
    skill_input,
):
    source_fixture = generate_synthetic_sources(seed=int(seed_input.value))
    pipeline_result = run_pipeline(
        source_fixture.batches,
        fixture_version=source_fixture.version,
        seed=source_fixture.seed,
        retry_counts={source: 0 for source in source_fixture.batches},
    )
    fit_preferences = FitPreferences(
        skill_tags=tuple(skill_input.value),
        engagement_types=tuple(engagement_input.value),
        remote_preferred=bool(remote_input.value),
        minimum_value_usd=float(minimum_value_input.value),
    )
    scored_opportunities = score_opportunities(
        pipeline_result.opportunities,
        fit_preferences,
    )
    return pipeline_result, scored_opportunities, source_fixture


@app.cell
def _(pipeline_result, source_fixture):
    manifest = pipeline_result.manifest
    mo.vstack(
        [
            mo.md(
                "## Run evidence\n\n"
                f"- Fixture: **{source_fixture.version}**; seed "
                f"**{source_fixture.seed}**\n"
                f"- Inputs: **{manifest.input_count}**; accepted versions: "
                f"**{manifest.accepted_count}**; rejected: "
                f"**{manifest.rejected_count}**\n"
                f"- Canonical opportunities: **{manifest.output_count}**\n"
                f"- Canonical SHA-256: `{manifest.canonical_hash}`\n"
                f"- State SHA-256: `{manifest.state_hash}`"
            ),
            mo.callout(
                "Re-run with the same seed to reproduce the same canonical, "
                "rejection, and state hashes.",
                kind="info",
            ),
        ]
    )


@app.cell
def _(scored_opportunities):
    mo.vstack(
        [
            mo.md("## Transparent opportunity ranking"),
            render_table(
                scored_opportunities,
                "Canonical opportunities with additive contributions",
            ),
        ]
    )


@app.cell
def _(pipeline_result):
    if pipeline_result.rejected.empty:
        dead_letter_view = mo.callout(
            "No rejected source rows.",
            kind="success",
        )
    else:
        dead_letter_view = mo.vstack(
            [
                mo.md("## Controlled dead-letter ledger"),
                render_table(
                    pipeline_result.rejected,
                    "Rejected synthetic rows",
                ),
            ]
        )
    dead_letter_view


@app.cell
def _(pipeline_result, scored_opportunities):
    mo.vstack(
        [
            mo.md("## Explicit safe downloads"),
            mo.hstack(
                [
                    mo.download(
                        data=lambda: dataframe_to_safe_csv(scored_opportunities),
                        filename="scored_opportunities.csv",
                        mimetype="text/csv",
                        label="Download scored opportunities",
                    ),
                    mo.download(
                        data=lambda: dataframe_to_safe_csv(pipeline_result.rejected),
                        filename="rejected_records.csv",
                        mimetype="text/csv",
                        label="Download dead letters",
                    ),
                    mo.download(
                        data=lambda: manifest_to_json(pipeline_result.manifest),
                        filename="run_manifest.json",
                        mimetype="application/json",
                        label="Download run manifest",
                    ),
                ],
                justify="start",
            ),
        ]
    )


if __name__ == "__main__":
    app.run()

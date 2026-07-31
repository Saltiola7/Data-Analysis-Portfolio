# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#     "marimo==0.23.15",
#     "pandas==3.0.5",
# ]
# ///
"""Interactive Marimo explorer for the synthetic wellness pipeline."""

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")

with app.setup:
    import html as _html

    import marimo as mo

    from wellness_data_pipeline import (
        NormalizationError,
        SchemaError,
        UploadError,
        audit_to_json,
        dataframe_to_safe_csv,
        generate_synthetic_fixture,
        read_csv_upload,
        run_pipeline,
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
    # Synthetic Wellness Data Pipeline

    **Data Engineer certification case study**

    Explore a deterministic, schema-governed pipeline using bundled synthetic data or four bounded CSV uploads. Processing stays in the active notebook runtime; this app performs no network requests and stores no uploaded data.

    This engineering demonstration is not a medical product and provides no health advice.
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
    use_uploads = mo.ui.switch(
        value=False,
        label="Use uploaded CSV files instead of bundled synthetic data",
    )
    participants_upload = mo.ui.file(
        filetypes=[".csv"],
        kind="area",
        max_size=2_000_000,
        label="Participants CSV (maximum 2 MB)",
    )
    programs_upload = mo.ui.file(
        filetypes=[".csv"],
        kind="area",
        max_size=2_000_000,
        label="Programs CSV (maximum 2 MB)",
    )
    signals_upload = mo.ui.file(
        filetypes=[".csv"],
        kind="area",
        max_size=2_000_000,
        label="Daily signals CSV (maximum 2 MB)",
    )
    interventions_upload = mo.ui.file(
        filetypes=[".csv"],
        kind="area",
        max_size=2_000_000,
        label="Interventions CSV (maximum 2 MB)",
    )
    return (
        interventions_upload,
        participants_upload,
        programs_upload,
        seed_input,
        signals_upload,
        use_uploads,
    )


@app.cell
def _(  # noqa: PLR0913, PLR0917
    interventions_upload,
    participants_upload,
    programs_upload,
    seed_input,
    signals_upload,
    use_uploads,
):
    mo.vstack(
        [
            mo.hstack([seed_input, use_uploads], justify="start"),
            mo.accordion(
                {
                    "Optional CSV uploads": mo.vstack(
                        [
                            mo.callout(
                                "Enable uploads only after selecting all four files. "
                                "Files are read in memory and are never written by the app.",
                                kind="info",
                            ),
                            participants_upload,
                            programs_upload,
                            signals_upload,
                            interventions_upload,
                        ]
                    )
                }
            ),
        ]
    )


@app.cell
def _(  # noqa: PLR0913, PLR0917
    interventions_upload,
    participants_upload,
    programs_upload,
    seed_input,
    signals_upload,
    use_uploads,
):
    pipeline_result = None
    input_status = None
    input_label = ""

    if use_uploads.value:
        uploads_ready = all(
            upload.value
            for upload in (
                participants_upload,
                programs_upload,
                signals_upload,
                interventions_upload,
            )
        )
        if not uploads_ready:
            input_status = mo.callout(
                "Select participants, programs, daily signals, and interventions CSV files.",
                kind="warn",
            )
        else:
            try:
                uploaded_participants = read_csv_upload(participants_upload.contents())
                uploaded_programs = read_csv_upload(programs_upload.contents())
                uploaded_signals = read_csv_upload(signals_upload.contents())
                uploaded_interventions = read_csv_upload(interventions_upload.contents())
                pipeline_result = run_pipeline(
                    uploaded_participants,
                    uploaded_programs,
                    uploaded_signals,
                    uploaded_interventions,
                )
                input_label = "Uploaded CSV files"
                input_status = mo.callout(
                    "Uploaded files validated and processed in memory.",
                    kind="success",
                )
            except (SchemaError, NormalizationError, UploadError) as exc:
                input_status = mo.callout(
                    f"Input validation failed: {exc}",
                    kind="danger",
                )
    else:
        synthetic_fixture = generate_synthetic_fixture(seed=int(seed_input.value))
        pipeline_result = run_pipeline(
            synthetic_fixture.participants,
            synthetic_fixture.programs,
            synthetic_fixture.daily_signals,
            synthetic_fixture.interventions,
        )
        input_label = (
            f"Bundled {synthetic_fixture.generator_version}; seed {synthetic_fixture.seed}"
        )
        input_status = mo.callout(
            "Deterministic synthetic fixture processed.",
            kind="success",
        )
    return input_label, input_status, pipeline_result


@app.cell
def _(input_label, input_status, pipeline_result):
    if pipeline_result is None:
        quality_summary = input_status
    else:
        audit = pipeline_result.audit
        quality_summary = mo.vstack(
            [
                input_status,
                mo.md(
                    "## Quality evidence\n\n"
                    f"**Source:** {input_label}\n\n"
                    f"- Curated participant-days: **{audit['output_count']}**\n"
                    "- Accepted daily signals: "
                    f"**{audit['accepted_counts']['daily_signals']}**\n"
                    "- Rejected records: "
                    f"**{sum(audit['rejected_counts'].values())}**\n"
                    f"- Schema version: **{audit['schema_version']}**"
                ),
            ]
        )
    quality_summary


@app.cell
def _(pipeline_result):
    if pipeline_result is None:
        curated_view = mo.md("Curated data appears after valid inputs are available.")
    else:
        curated_view = mo.vstack(
            [
                mo.md("## Curated participant-day table"),
                render_table(
                    pipeline_result.participant_days,
                    "Accepted participant-days",
                ),
            ]
        )
    curated_view


@app.cell
def _(pipeline_result):
    if pipeline_result is None:
        rejected_view = mo.md("Rejected-record evidence appears after pipeline execution.")
    elif pipeline_result.rejected_records.empty:
        rejected_view = mo.callout("No rejected records.", kind="success")
    else:
        rejected_view = mo.vstack(
            [
                mo.md("## Rejected-record ledger"),
                render_table(
                    pipeline_result.rejected_records,
                    "Rejected records",
                ),
            ]
        )
    rejected_view


@app.cell
def _(pipeline_result):
    if pipeline_result is None:
        download_view = mo.md("Downloads appear after successful pipeline execution.")
    else:
        download_view = mo.vstack(
            [
                mo.md("## Explicit downloads"),
                mo.hstack(
                    [
                        mo.download(
                            data=lambda: dataframe_to_safe_csv(pipeline_result.participant_days),
                            filename="participant_days.csv",
                            mimetype="text/csv",
                            label="Download curated CSV",
                        ),
                        mo.download(
                            data=lambda: dataframe_to_safe_csv(pipeline_result.rejected_records),
                            filename="rejected_records.csv",
                            mimetype="text/csv",
                            label="Download rejected ledger",
                        ),
                        mo.download(
                            data=lambda: audit_to_json(pipeline_result),
                            filename="audit.json",
                            mimetype="application/json",
                            label="Download audit JSON",
                        ),
                    ],
                    justify="start",
                ),
            ]
        )
    download_view


if __name__ == "__main__":
    app.run()

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.15",
#     "numpy==2.5.1",
#     "pandas==3.0.5",
#     "scikit-learn==1.9.0",
# ]
# ///
"""Interactive Marimo explorer for synthetic content classification."""

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")


@app.cell
def _():
    import html as _html

    import marimo as mo
    import pandas as pd

    from content_performance_classifier import (
        InputValidationError,
        audit_to_json,
        evaluate_at_threshold,
        evaluate_reserved_test,
        generate_synthetic_content,
        predictions_to_safe_csv,
        read_content_csv,
        train_classifier,
    )

    def render_table(frame, columns, caption, *, row_limit=200):
        rows = frame.loc[:, [key for key, _ in columns]].head(row_limit).to_dict(orient="records")
        if not rows:
            return mo.md("*No rows are available.*")

        def _cell(value):
            rendered = "" if value is None else str(value)
            return _html.escape(rendered).replace("\n", "<br>")

        safe_caption = _html.escape(caption)
        header = "".join(
            f'<th scope="col" style="text-align:left;padding:0.5rem;'
            f'border-bottom:1px solid var(--sl-color-neutral-300)">{_cell(label)}</th>'
            for _, label in columns
        )
        body = "".join(
            "<tr>"
            + "".join(
                f'<td style="vertical-align:top;padding:0.5rem;'
                f'border-bottom:1px solid var(--sl-color-neutral-200)">'
                f"{_cell(row.get(key, ''))}</td>"
                for key, _ in columns
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
            f"{safe_caption}</caption><thead><tr>{header}</tr></thead>"
            f"<tbody>{body}</tbody></table>{limit_note}</div>"
        )

    return (
        InputValidationError,
        audit_to_json,
        evaluate_at_threshold,
        evaluate_reserved_test,
        generate_synthetic_content,
        mo,
        pd,
        predictions_to_safe_csv,
        read_content_csv,
        render_table,
        train_classifier,
    )


@app.cell
def _(mo):
    mo.md("""
    # Content Performance Classifier

    Explore leakage-safe classification, baseline comparison, calibration,
    decision thresholds, slice performance, and error evidence. Default data is
    deterministic and synthetic. Optional CSV uploads stay in the active
    notebook runtime; classifier code does not transmit or persist upload
    content. The runtime may fetch application dependencies. In a server-hosted
    notebook, processing may occur remotely. Use the WASM build when
    browser-only processing is required.

    Synthetic performance demonstrates method. It does **not** estimate
    production uplift or external validity.
    """)


@app.cell
def _(mo):
    seed_input = mo.ui.number(
        start=0,
        stop=999_999,
        step=1,
        value=2026,
        label="Seed",
    )
    row_input = mo.ui.number(
        start=100,
        stop=5_000,
        step=100,
        value=600,
        label="Synthetic rows",
    )
    threshold_input = mo.ui.slider(
        start=0.05,
        stop=0.95,
        step=0.05,
        value=0.5,
        label="Decision threshold",
        show_value=True,
    )
    use_upload = mo.ui.switch(
        value=False,
        label="Use uploaded labeled CSV",
    )
    content_upload = mo.ui.file(
        filetypes=[".csv"],
        kind="area",
        max_size=5_000_000,
        label="Content observations CSV (maximum 5 MB and 5,000 rows)",
    )
    return content_upload, row_input, seed_input, threshold_input, use_upload


@app.cell
def _(content_upload, mo, row_input, seed_input, threshold_input, use_upload):
    mo.vstack(
        [
            mo.hstack(
                [seed_input, row_input, threshold_input, use_upload],
                justify="start",
            ),
            mo.accordion(
                {
                    "Optional runtime-only upload": mo.vstack(
                        [
                            mo.callout(
                                "Upload a labeled CSV matching the documented feature contract. "
                                "The file is parsed in memory and never written by this app.",
                                kind="info",
                            ),
                            content_upload,
                        ]
                    )
                }
            ),
        ]
    )


@app.cell
def _(
    InputValidationError,
    content_upload,
    evaluate_at_threshold,
    evaluate_reserved_test,
    generate_synthetic_content,
    mo,
    read_content_csv,
    row_input,
    seed_input,
    threshold_input,
    train_classifier,
    use_upload,
):
    classifier_artifact = None
    reserved_test_result = None
    validation_result = None
    input_status = None
    source_label = ""

    try:
        if use_upload.value:
            if not content_upload.value:
                input_status = mo.callout("Select a labeled CSV file.", kind="warn")
            else:
                input_frame = read_content_csv(content_upload.contents())
                classifier_artifact = train_classifier(
                    input_frame,
                    seed=int(seed_input.value),
                )
                source_label = "Runtime-only uploaded CSV"
        else:
            content_fixture = generate_synthetic_content(
                seed=int(seed_input.value),
                rows=int(row_input.value),
            )
            classifier_artifact = train_classifier(
                content_fixture.frame,
                seed=int(seed_input.value),
            )
            source_label = (
                f"{content_fixture.fixture_version}; seed {content_fixture.seed}; "
                f"{content_fixture.rows} rows"
            )

        if classifier_artifact is not None:
            validation_result = evaluate_at_threshold(
                classifier_artifact,
                threshold=float(threshold_input.value),
            )
            reserved_test_result = evaluate_reserved_test(classifier_artifact)
            input_status = mo.callout(
                "Input validated. Slider explores validation evidence; reserved test "
                "evidence stays fixed at the validation-selected reporting threshold.",
                kind="success",
            )
    except (InputValidationError, ValueError) as exc:
        input_status = mo.callout(f"Input validation failed: {exc}", kind="danger")
    return (
        classifier_artifact,
        input_status,
        reserved_test_result,
        source_label,
        validation_result,
    )


@app.cell
def _(
    input_status,
    mo,
    pd,
    render_table,
    reserved_test_result,
    source_label,
    validation_result,
):
    if validation_result is None or reserved_test_result is None:
        summary_view = input_status
    else:
        metric_order = [
            "baseline_accuracy",
            "accuracy",
            "balanced_accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "brier_score",
        ]
        validation_metrics = (validation_result.metrics[name] for name in metric_order)
        validation_metric_frame = pd.DataFrame(
            {"metric": metric_order, "value": list(validation_metrics)}
        )
        reserved_metric_frame = pd.DataFrame(
            {
                "metric": metric_order,
                "value": [reserved_test_result.metrics[name] for name in metric_order],
            }
        )
        summary_view = mo.vstack(
            [
                input_status,
                mo.md(
                    "## Validation evidence\n\n"
                    f"**Source:** {source_label}\n\n"
                    f"**Exploratory threshold:** {validation_result.threshold:.2f}"
                ),
                render_table(
                    validation_metric_frame,
                    (("metric", "Metric"), ("value", "Value")),
                    "Validation metrics",
                ),
                mo.md(
                    "## Reserved test evidence\n\n"
                    "This partition is not used by the slider or threshold selection.\n\n"
                    f"**Validation-selected reporting threshold:** "
                    f"{reserved_test_result.threshold:.2f}"
                ),
                render_table(
                    reserved_metric_frame,
                    (("metric", "Metric"), ("value", "Value")),
                    "Reserved test metrics",
                ),
            ]
        )
    summary_view


@app.cell
def _(mo, render_table, validation_result):
    if validation_result is None:
        calibration_view = mo.md("Calibration evidence appears after valid input.")
    else:
        calibration_view = mo.vstack(
            [
                mo.md(
                    "## Validation calibration evidence\n\n"
                    "Brier score and observed outcome rates reveal probability quality."
                ),
                render_table(
                    validation_result.calibration,
                    (
                        ("bin_lower", "Bin lower"),
                        ("bin_upper", "Bin upper"),
                        ("support", "Support"),
                        ("mean_probability", "Mean probability"),
                        ("observed_rate", "Observed rate"),
                    ),
                    "Ten equal-width probability bins",
                ),
            ]
        )
    calibration_view


@app.cell
def _(mo, render_table, validation_result):
    if validation_result is None:
        slice_view = mo.md("Slice evidence appears after valid input.")
    else:
        slice_view = mo.vstack(
            [
                mo.md(
                    "## Validation slice evidence\n\n"
                    "Small slices are labeled and should not be overinterpreted."
                ),
                render_table(
                    validation_result.slices,
                    (
                        ("dimension", "Dimension"),
                        ("value", "Category"),
                        ("support", "Support"),
                        ("precision", "Precision"),
                        ("recall", "Recall"),
                        ("false_positive", "False positive"),
                        ("false_negative", "False negative"),
                        ("small_slice", "Small slice"),
                    ),
                    "Topic-family and content-type performance",
                ),
            ]
        )
    slice_view


@app.cell
def _(mo, render_table, validation_result):
    if validation_result is None:
        error_view = mo.md("Error evidence appears after valid input.")
    else:
        error_rows = validation_result.predictions.loc[
            validation_result.predictions["error_type"].isin(["false_positive", "false_negative"])
        ]
        error_view = mo.vstack(
            [
                mo.md("## Validation error review"),
                render_table(
                    error_rows,
                    (
                        ("content_id", "Content ID"),
                        ("probability", "Probability"),
                        ("threshold", "Threshold"),
                        ("predicted_class", "Predicted"),
                        ("actual_class", "Actual"),
                        ("error_type", "Error type"),
                    ),
                    "False-positive and false-negative decisions",
                    row_limit=100,
                ),
            ]
        )
    error_view


@app.cell
def _(
    audit_to_json,
    classifier_artifact,
    mo,
    predictions_to_safe_csv,
    validation_result,
):
    if validation_result is None or classifier_artifact is None:
        download_view = mo.md("Downloads appear after successful evaluation.")
    else:
        download_view = mo.vstack(
            [
                mo.md("## Explicit downloads"),
                mo.hstack(
                    [
                        mo.download(
                            data=lambda: predictions_to_safe_csv(validation_result),
                            filename="content_validation_predictions.csv",
                            mimetype="text/csv",
                            label="Download safe predictions CSV",
                        ),
                        mo.download(
                            data=lambda: audit_to_json(
                                classifier_artifact,
                                validation_result,
                            ),
                            filename="content_classifier_audit.json",
                            mimetype="application/json",
                            label="Download metadata-only audit JSON",
                        ),
                    ],
                    justify="start",
                ),
            ]
        )
    download_view


if __name__ == "__main__":
    app.run()

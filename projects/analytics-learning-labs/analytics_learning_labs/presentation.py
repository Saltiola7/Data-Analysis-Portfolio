"""Accessible, dependency-light HTML evidence for Marimo learning labs."""

from __future__ import annotations

import html
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from analytics_learning_labs.contracts import AnalysisResult

LabState = Literal["success", "validation-error", "unexpected-error"]
MAXIMUM_SEED = 999_999


@dataclass(frozen=True)
class LabRun:
    """Fail-closed result of generating and analyzing one synthetic fixture."""

    frame: pd.DataFrame | None
    result: AnalysisResult | None
    seed: int | None
    state: LabState
    message: str


def _normalize_seed(seed: object) -> int:
    if isinstance(seed, bool) or not isinstance(seed, (int, float)):
        raise ValueError("seed must be an integer from 0 to 999999")
    numeric_seed = float(seed)
    if not math.isfinite(numeric_seed) or not numeric_seed.is_integer():
        raise ValueError("seed must be an integer from 0 to 999999")
    normalized_seed = int(numeric_seed)
    if not 0 <= normalized_seed <= MAXIMUM_SEED:
        raise ValueError("seed must be an integer from 0 to 999999")
    return normalized_seed


def run_lab(
    generator: Callable[..., pd.DataFrame],
    analyzer: Callable[[pd.DataFrame], AnalysisResult],
    *,
    seed: object,
) -> LabRun:
    """Run a lab without exposing an unexpected exception or partial result."""

    try:
        normalized_seed = _normalize_seed(seed)
        frame = generator(seed=normalized_seed)
        result = analyzer(frame)
    except (TypeError, ValueError) as error:
        return LabRun(
            frame=None,
            result=None,
            seed=None,
            state="validation-error",
            message=f"Validation error: {error}",
        )
    except Exception:
        return LabRun(
            frame=None,
            result=None,
            seed=None,
            state="unexpected-error",
            message="Unexpected error: analysis could not run safely.",
        )
    return LabRun(
        frame=frame,
        result=result,
        seed=normalized_seed,
        state="success",
        message="Success: analysis ready.",
    )


def render_fixture_identity(run: LabRun) -> str:
    """Render stable browser evidence for fixture identity and grain."""

    if run.frame is None or run.result is None:
        return f'<p data-testid="fixture-identity">{html.escape(run.message)}</p>'
    generator_version = html.escape(str(run.frame.attrs.get("generator_version", "unknown")))
    fixture_sha256 = html.escape(str(run.frame.attrs.get("fixture_sha256", "unknown")))
    grain = html.escape(run.result.grain)
    return (
        '<p data-testid="fixture-identity" aria-live="polite">'
        f"<strong>Fixture:</strong> generator_version={generator_version}; "
        f"seed={run.seed}; rows={len(run.frame)}; grain={grain}; "
        f"sha256={fixture_sha256}; pandas={html.escape(pd.__version__)}</p>"
    )


def render_metric_cards(metrics: Mapping[str, str | int | float]) -> str:
    """Render compact metric evidence without a chart dependency."""

    cards = "".join(
        '<div style="border:1px solid var(--sl-color-neutral-300);'
        'border-radius:0.5rem;padding:0.75rem;min-width:10rem">'
        f'<div style="font-size:0.82rem">{html.escape(key.replace("_", " ").title())}</div>'
        f'<strong style="font-size:1.2rem">{html.escape(str(value))}</strong>'
        "</div>"
        for key, value in metrics.items()
    )
    return (
        '<section aria-label="Analysis metrics" style="display:flex;flex-wrap:wrap;'
        f'gap:0.75rem">{cards}</section>'
    )


def render_captioned_table(
    frame: pd.DataFrame,
    *,
    caption: str,
    test_id: str,
    columns: Sequence[str] | None = None,
    row_limit: int = 20,
) -> str:
    """Render a semantic table with a visible caption and bounded rows."""

    selected = list(columns) if columns is not None else list(frame.columns)
    visible = frame.loc[:, selected].head(row_limit)
    header = "".join(
        f'<th scope="col" style="text-align:left;padding:0.45rem;'
        f'border-bottom:1px solid var(--sl-color-neutral-300)">'
        f"{html.escape(column.replace('_', ' ').title())}</th>"
        for column in selected
    )
    rows = "".join(
        "<tr>"
        + "".join(
            '<td style="vertical-align:top;padding:0.45rem;'
            'border-bottom:1px solid var(--sl-color-neutral-200)">'
            f"{html.escape(str(value))}</td>"
            for value in row
        )
        + "</tr>"
        for row in visible.itertuples(index=False, name=None)
    )
    if visible.empty:
        rows = f'<tr><td colspan="{max(1, len(selected))}">No rows are available.</td></tr>'
    limit_note = (
        f"<p>Showing first {row_limit} of {len(frame)} rows.</p>" if len(frame) > row_limit else ""
    )
    safe_test_id = html.escape(test_id, quote=True)
    return (
        '<div style="max-width:100%;overflow:auto;max-height:34rem">'
        f'<table data-testid="{safe_test_id}" '
        'style="width:100%;border-collapse:collapse">'
        f'<caption data-testid="{safe_test_id}-caption" '
        'style="text-align:left;font-weight:650;padding:0.5rem 0">'
        f"{html.escape(caption)}</caption>"
        f"<thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"
        f"{limit_note}</div>"
    )


def render_bar_evidence(
    frame: pd.DataFrame,
    *,
    label_column: str,
    value_column: str,
    title: str,
    description: str,
    limit: int = 8,
) -> str:
    """Render a small accessible SVG bar view from aggregated evidence."""

    source = frame.loc[:, [label_column, value_column]].head(limit)
    values: list[float] = []
    for value in source[value_column]:
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError("bar evidence values must be finite")
        if numeric < 0:
            raise ValueError("bar evidence values must be non-negative")
        values.append(numeric)
    maximum = max(values, default=1.0) or 1.0
    width = 720
    left = 170
    bar_width = width - left - 90
    row_height = 38
    height = max(100, 58 + row_height * len(source))
    bars: list[str] = []
    for index, ((label, _), value) in enumerate(
        zip(source.itertuples(index=False, name=None), values, strict=True)
    ):
        y = 42 + index * row_height
        scaled = round(bar_width * value / maximum, 2)
        bars.append(
            f'<text x="4" y="{y + 16}" font-size="13" fill="currentColor">'
            f"{html.escape(str(label))}</text>"
            f'<rect x="{left}" y="{y}" width="{scaled}" height="22" '
            'rx="3" fill="#2563eb"></rect>'
            f'<text x="{left + scaled + 7}" y="{y + 16}" '
            'font-size="13" fill="currentColor">'
            f"{html.escape(f'{value:g}')}</text>"
        )
    safe_title = html.escape(title)
    safe_description = html.escape(description)
    return (
        f'<svg role="img" aria-labelledby="bar-title bar-description" '
        f'viewBox="0 0 {width} {height}" style="width:100%;max-width:720px;'
        'min-height:8rem">'
        f'<title id="bar-title">{safe_title}</title>'
        f'<desc id="bar-description">{safe_description}</desc>'
        f"{''.join(bars)}</svg>"
    )

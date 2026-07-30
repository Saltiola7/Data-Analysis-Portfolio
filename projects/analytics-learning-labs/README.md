# Analytics Learning Labs

Five small, browser-runnable Marimo applications that revisit historical
analytical learning themes through independently written code and deterministic
synthetic data.

These labs support the portfolio's three flagships. They demonstrate analytical
grain, validation, reproducibility, and communication; they are not represented
as production systems or as migrated coursework.

## Applications

| Lab | Source | Run | Canonical grain |
|---|---|---|---|
| Airline Delay Quality Lab | [`apps/airline_delays.py`](apps/airline_delays.py) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/airline_delays.py/wasm) | One fictional flight |
| Synthetic Health Risk Quality Lab | [`apps/synthetic_cohort.py`](apps/synthetic_cohort.py) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/synthetic_cohort.py/wasm) | One unique fictional profile after duplicate audit |
| Restaurant Location Quality Lab | [`apps/restaurant_locations.py`](apps/restaurant_locations.py) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/restaurant_locations.py/wasm) | One fictional location record |
| Streaming Catalog Explorer | [`apps/streaming_catalog.py`](apps/streaming_catalog.py) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/streaming_catalog.py/wasm) | One fictional catalog title |
| Judo Medal Explorer | [`apps/sports_outcomes.py`](apps/sports_outcomes.py) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/sports_outcomes.py/wasm) | One fictional athlete-event |

Each Molab URL points to canonical `main` source. Molab derives an on-demand
browser runtime from that source; this repository does not operate a data
collection backend.

### Airline Delay Quality Lab

Builds a fictional flight-grain fixture and summarizes arrival-delay components
and cancellations by carrier. Non-negative delay-component contracts and a
unique flight identifier keep aggregation denominators explicit. Mean delay
values use completed flights only; cancellations remain visible in flight,
cancellation, and operational on-time denominators.

### Synthetic Health Risk Quality Lab

Audits repeated fictional profiles before summarizing ordinal associations.
Repeated records are deduplicated only when every profile attribute agrees;
conflicting repeats fail validation. The app distinguishes source-record and
unique-profile denominators. Its output is descriptive educational evidence
only: it has no clinical validity, makes no diagnosis, implies no causality,
and recommends no medical action.

### Restaurant Location Quality Lab

Validates fictional latitude and longitude values, separates accepted records
from unresolved ones, and exposes the unresolved ledger. Invalid coordinates
are never silently repaired or replaced with invented locations. The default
fixture deliberately includes bounded missing-latitude and missing-longitude
examples so both paths remain visible.

### Streaming Catalog Explorer

Summarizes a fictional catalog by release period, genre, content type, and
duration while preserving one-title grain. No commercial catalog record or
licensed entertainment dataset is included.

### Judo Medal Explorer

Explores medal rates across fictional teams, continents, and weight classes at
declared athlete-event grain. Identifiers are synthetic, and the app contains
no athlete names or historical competition records. A repeated fictional
athlete retains one team, continent, and weight class across events.

## Shared evidence contract

Every app:

1. starts from a deterministic default fixture with a visible generator version
   and integer seed;
2. validates required columns, row bounds, null and duplicate grain keys, and
   lab-specific value boundaries before analysis;
3. displays fixture identity, grain, metrics, limitations, and a captioned
   table;
4. recomputes in browser memory when the seed changes;
5. exposes success, validation-error, and unexpected-error states in text while
   Marimo supplies its native pending-cell indicator during recomputation;
6. makes no application-initiated external data, API, owner-backend, telemetry,
   or credential request after the Molab/Pyodide runtime dependencies load.

The five apps share the `analytics_learning_labs` package for fixture contracts,
synthetic generators, analysis, and presentation helpers. One project-local
`pyproject.toml` and `uv.lock` define the executable environment. The host lock,
PEP 723 headers, and executed browser evidence agree on pandas 3.0.2. Direct
Molab entrypoints install the shared package from a deterministic wheel pinned
by `browser-wheel-lock.json` to an immutable Git commit and SHA-256.

## Reproduce locally

From this directory:

```bash
uv sync --locked
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen marimo check --strict apps/*.py
```

From the repository root, validate the browser wheel, immutable commit blob,
package source, dependency metadata, and RECORD:

```bash
uv run --frozen python scripts/verify_browser_wheel.py
```

Open one app for interactive review:

```bash
uv run --frozen marimo edit apps/airline_delays.py
```

The repository quality workflow also executes every app as an HTML-WASM export,
validates the embedded local package wheel, exercises each runtime in Chromium,
and repeats the five learning-lab journeys through exact-commit Molab URLs.

## Data, privacy, and provenance

All rows are newly generated fictional records. No historical notebook dataset,
employer or client record, assessment material, personal data, or private
infrastructure enters the package or browser runtime. The apps accept no upload
and persist no visitor state.

See [PROVENANCE.md](PROVENANCE.md) for the theme-only source lineage and
clean-room method, [the repository data record](../../DATA_PROVENANCE.md), and
[professional certification evidence](../../CERTIFICATIONS.md).

## Limitations

- Synthetic fixtures prove behavior and reproducibility, not external
  validity.
- Summaries are intentionally compact and do not replace domain-specific
  operational analysis.
- The health lab is not a medical model or clinical decision tool.
- WCAG 2.2 AA is a target, not claimed conformance. In Marimo 0.23.15's
  exported number control, the visible `Seed` label is correctly associated
  through `label[for]`, but the generated `aria-label` contains rendered markup
  instead of the plain accessible name `Seed`.
- Molab availability depends on GitHub source compatibility with Marimo and
  Pyodide; local locked validation remains the reproducibility authority.

## License

New source and documentation in this project are available under the
repository's [MIT License](../../LICENSE). No historical notebook, assessment
artifact, or third-party dataset is relicensed or redistributed.

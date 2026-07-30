# Development evidence

## Red

Date: 2026-07-29

Command:

```bash
python -m pytest -p no:cacheprovider -q projects/public-sector-opportunity-pipeline/tests
```

Expected result: failed during collection because the implementation package
did not exist.

Decisive output:

```text
ModuleNotFoundError: No module named 'public_sector_opportunity_pipeline'
4 errors in 0.37s
```

Review hardening added focused regression tests before changing the
implementation. They covered cross-run same-timestamp tie-breaking, fractional
timestamps, canonical-row semantics, pre-copy volume checks, hostile value
bounds, finite retry delays, whitespace-aware CSV protection, and strict fit
preferences.

```bash
uv run --frozen pytest -q \
  tests/test_pipeline.py::test_same_timestamp_hash_tie_break_is_stable_across_incremental_runs \
  tests/test_pipeline.py::test_fractional_update_timestamp_is_retained_in_output_and_state \
  tests/test_pipeline.py::test_source_volume_is_rejected_before_record_copying \
  tests/test_pipeline.py::test_hostile_source_value_type_fails_before_dead_letter_hashing \
  tests/test_pipeline.py::test_oversized_source_text_fails_at_input_boundary \
  tests/test_pipeline.py::test_existing_canonical_rows_are_semantically_validated \
  tests/test_retries.py::test_adapter_source_volume_is_rejected_before_record_copying \
  tests/test_retries.py::test_invalid_retry_policy_fails_at_boundary \
  tests/test_scoring_exports.py::test_safe_csv_neutralizes_formula_prefixes_without_changing_numbers \
  tests/test_scoring_exports.py::test_scoring_preferences_fail_closed_on_invalid_types_and_values
```

Expected result:

```text
25 failed, 4 passed in 0.49s
```

One additional red test showed that an extreme integer reached `float()` and
raised `OverflowError` before the source boundary rejected it:

```text
1 failed in 0.40s
```

## Green

Date: 2026-07-29

```bash
uv lock --check
uv run --frozen pytest -q
uv run ruff check .
uv run ruff format --check .
uv run marimo check --strict app.py
uv run marimo export html app.py -o public/index.html
```

Results:

```text
66 passed
All checks passed!
21 files already formatted
strict Marimo check passed
executed WASM export passed package and embedded-error validation
```

Browser-core isolation was also validated in a clean environment with only
runtime dependencies:

```bash
uv run --isolated --no-dev python -c "import importlib.util, runpy; assert importlib.util.find_spec('prefect') is None; runpy.run_path('app.py', run_name='portfolio_validation')"
```

The portable `run_prefect_pipeline()` path matches core canonical, rejection,
state, and hash evidence, and flow construction is tested. The optional
`use_engine=True` path is not claimed as exercised by this evidence packet.

A headless Chromium gate toggles the remote-preference control and confirms
that additive rule contributions recompute without console or page errors.

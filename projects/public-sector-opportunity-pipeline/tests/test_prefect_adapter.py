from __future__ import annotations

import sys

from pandas.testing import assert_frame_equal

from public_sector_opportunity_pipeline import (
    generate_synthetic_sources,
    run_pipeline,
)
from public_sector_opportunity_pipeline.prefect_adapter import (
    build_prefect_flow,
    run_prefect_pipeline,
)


def test_prefect_adapter_matches_portable_core() -> None:
    fixture = generate_synthetic_sources(seed=2026)

    core = run_pipeline(fixture.batches)
    orchestrated = run_prefect_pipeline(fixture)

    assert_frame_equal(core.opportunities, orchestrated.opportunities)
    assert_frame_equal(core.rejected, orchestrated.rejected)
    assert core.state == orchestrated.state
    assert core.manifest.canonical_hash == orchestrated.manifest.canonical_hash
    assert core.manifest.rejection_hash == orchestrated.manifest.rejection_hash
    assert core.manifest.state_hash == orchestrated.manifest.state_hash

    flow = build_prefect_flow()
    assert flow.name == "public-sector-opportunity-pipeline"
    assert callable(flow.fn)


def test_importing_core_does_not_import_prefect() -> None:
    sys.modules.pop("prefect", None)
    sys.modules.pop("public_sector_opportunity_pipeline", None)

    __import__("public_sector_opportunity_pipeline")

    assert "prefect" not in sys.modules

"""Independent deterministic synthetic content generator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .contracts import CONTENT_COLUMNS, CONTENT_TYPES, TOPIC_FAMILIES
from .hashing import hash_frame
from .models import ContentFixture

FIXTURE_VERSION = "content-performance-synthetic-v1"
MIN_SYNTHETIC_ROWS = 40
MAX_SYNTHETIC_ROWS = 5_000


def generate_synthetic_content(seed: int = 2026, rows: int = 600) -> ContentFixture:
    """Generate fictional content features and bounded-noise binary outcomes."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if (
        isinstance(rows, bool)
        or not isinstance(rows, int)
        or not MIN_SYNTHETIC_ROWS <= rows <= MAX_SYNTHETIC_ROWS
    ):
        raise ValueError(
            f"rows must be an integer from {MIN_SYNTHETIC_ROWS} through {MAX_SYNTHETIC_ROWS}"
        )

    rng = np.random.default_rng(seed)
    topic_values = np.array(sorted(TOPIC_FAMILIES), dtype=object)
    type_values = np.array(sorted(CONTENT_TYPES), dtype=object)
    topic_family = rng.choice(topic_values, size=rows, replace=True)
    content_type = rng.choice(type_values, size=rows, replace=True)

    word_count = np.clip(rng.lognormal(mean=7.15, sigma=0.47, size=rows), 200, 5_000).round()
    readability_score = np.clip(rng.normal(loc=61, scale=14, size=rows), 0, 100).round(2)
    age_days = rng.integers(0, 1_201, size=rows)
    internal_link_count = np.clip(rng.poisson(lam=9, size=rows), 0, 100)
    entity_count = np.clip(rng.poisson(lam=16, size=rows), 0, 100)
    query_coverage = np.clip(rng.beta(a=2.4, b=2.0, size=rows), 0, 1).round(4)
    update_cadence = np.clip(rng.poisson(lam=4, size=rows), 0, 24)

    topic_effect = {
        "analytics": 0.25,
        "commerce": -0.05,
        "operations": -0.20,
        "strategy": 0.10,
        "technical": 0.35,
    }
    type_effect = {
        "case_study": 0.30,
        "comparison": 0.10,
        "guide": 0.25,
        "reference": -0.20,
        "tutorial": 0.05,
    }
    signal = (
        -2.15
        + 2.6 * query_coverage
        + 0.045 * internal_link_count
        + 0.025 * entity_count
        + 0.12 * update_cadence
        - 0.00125 * age_days
        + 0.00022 * word_count
        + 0.012 * (readability_score - 55)
        + np.array([topic_effect[value] for value in topic_family])
        + np.array([type_effect[value] for value in content_type])
    )
    probability = 1 / (1 + np.exp(-signal))
    noisy_probability = np.clip(0.04 + 0.92 * probability, 0.04, 0.96)
    high_engagement = rng.binomial(1, noisy_probability)

    frame = pd.DataFrame(
        {
            "content_id": [f"content-{index:06d}" for index in range(1, rows + 1)],
            "topic_family": topic_family,
            "content_type": content_type,
            "word_count": word_count.astype("int64"),
            "readability_score": readability_score,
            "age_days": age_days,
            "internal_link_count": internal_link_count,
            "entity_count": entity_count,
            "query_coverage": query_coverage,
            "update_cadence": update_cadence,
            "high_engagement": high_engagement.astype("int8"),
        },
        columns=CONTENT_COLUMNS,
    )
    readability_missing = np.arange(rows) % 17 == 0
    coverage_missing = np.arange(rows) % 23 == 0
    frame.loc[readability_missing, "readability_score"] = np.nan
    frame.loc[coverage_missing, "query_coverage"] = np.nan
    frame.attrs["fixture_version"] = FIXTURE_VERSION
    frame.attrs["fixture_seed"] = seed
    fixture_hash = hash_frame(frame)
    frame.attrs["fixture_hash"] = fixture_hash
    return ContentFixture(
        frame=frame,
        seed=seed,
        rows=rows,
        fixture_version=FIXTURE_VERSION,
        fixture_hash=fixture_hash,
    )

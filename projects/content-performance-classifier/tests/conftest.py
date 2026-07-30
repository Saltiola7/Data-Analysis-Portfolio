from __future__ import annotations

import pytest

from content_performance_classifier import (
    generate_synthetic_content,
    train_classifier,
)


@pytest.fixture(scope="session")
def fixture():
    return generate_synthetic_content(seed=2026, rows=600)


@pytest.fixture(scope="session")
def artifact(fixture):
    return train_classifier(fixture.frame, seed=2026)

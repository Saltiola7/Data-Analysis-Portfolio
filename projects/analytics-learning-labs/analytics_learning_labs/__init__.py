"""Deterministic synthetic fixtures and analyses for five public learning labs."""

from analytics_learning_labs.analysis import (
    analyze_airline_delays,
    analyze_restaurant_locations,
    analyze_sports_outcomes,
    analyze_streaming_catalog,
    analyze_synthetic_cohort,
)
from analytics_learning_labs.contracts import (
    AIRLINE_CONTRACT,
    COHORT_CONTRACT,
    RESTAURANT_CONTRACT,
    SPORTS_CONTRACT,
    STREAMING_CONTRACT,
    AnalysisResult,
    FixtureContract,
    validate_fixture,
)
from analytics_learning_labs.fixtures import (
    generate_airline_fixture,
    generate_cohort_fixture,
    generate_restaurant_fixture,
    generate_sports_fixture,
    generate_streaming_fixture,
)

__all__ = [
    "AIRLINE_CONTRACT",
    "COHORT_CONTRACT",
    "RESTAURANT_CONTRACT",
    "SPORTS_CONTRACT",
    "STREAMING_CONTRACT",
    "AnalysisResult",
    "FixtureContract",
    "analyze_airline_delays",
    "analyze_restaurant_locations",
    "analyze_sports_outcomes",
    "analyze_streaming_catalog",
    "analyze_synthetic_cohort",
    "generate_airline_fixture",
    "generate_cohort_fixture",
    "generate_restaurant_fixture",
    "generate_sports_fixture",
    "generate_streaming_fixture",
    "validate_fixture",
]

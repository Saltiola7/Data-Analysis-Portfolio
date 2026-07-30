"""Deterministic fictional source fixtures with no live-system lineage."""

from __future__ import annotations

import random

from public_sector_opportunity_pipeline.models import SourceFixture


def generate_synthetic_sources(seed: int = 2026) -> SourceFixture:
    """Generate two heterogeneous, versioned source batches."""

    generator = random.Random(seed)
    federal_value = generator.randrange(220_000, 281_000, 5_000)
    municipal_value = generator.randrange(140_000, 201_000, 5_000)

    federal: tuple[dict[str, object], ...] = (
        {
            "notice_id": "FED-1001",
            "notice_title": "Cloud Data Modernization Discovery",
            "bureau": "Civic Digital Services Office",
            "published_on": "2026-07-01",
            "closes_on": "2026-08-01",
            "work_location": "remote",
            "award_type": "task_order",
            "min_value_usd": 120_000,
            "max_value_usd": federal_value,
            "capabilities": ["Python", "GCP", "Data Engineering"],
            "modified_at": "2026-07-01T12:00:00Z",
        },
        {
            "notice_id": "FED-1001",
            "notice_title": "Cloud Data Modernization Delivery",
            "bureau": "Civic Digital Services Office",
            "published_on": "2026-07-01",
            "closes_on": "2026-08-08",
            "work_location": "remote",
            "award_type": "task_order",
            "min_value_usd": 140_000,
            "max_value_usd": federal_value + 20_000,
            "capabilities": ["Python", "GCP", "Data Engineering"],
            "modified_at": "2026-07-05T12:00:00Z",
        },
        {
            "notice_id": "FED-1002",
            "notice_title": "Search Evidence Taxonomy Prototype",
            "bureau": "Public Information Laboratory",
            "published_on": "2026-07-04",
            "closes_on": "2026-08-20",
            "work_location": "flexible",
            "award_type": "fixed_scope",
            "min_value_usd": 85_000,
            "max_value_usd": 155_000,
            "capabilities": ["Search", "AI", "Analytics"],
            "modified_at": "2026-07-04T16:00:00Z",
        },
        {
            "notice_id": None,
            "notice_title": "Intentionally invalid identity example",
            "bureau": "Fixture Quality Office",
            "published_on": "2026-07-06",
            "closes_on": "2026-08-30",
            "work_location": "remote",
            "award_type": "professional_services",
            "min_value_usd": 50_000,
            "max_value_usd": 75_000,
            "capabilities": ["Data Quality"],
            "modified_at": "2026-07-06T10:00:00Z",
        },
    )
    municipal: tuple[dict[str, object], ...] = (
        {
            "solicitation_number": "MUN-2001",
            "name": "Open Data Analytics Platform",
            "department": "Metro Innovation Lab",
            "posted_at": "2026-07-03",
            "deadline": "2026-08-15",
            "remote_policy": "hybrid",
            "engagement_model": "project",
            "budget_floor": 80_000,
            "budget_ceiling": municipal_value,
            "required_skills": "analytics|sql|python",
            "updated_at": "2026-07-03T09:30:00-05:00",
        },
        {
            "solicitation_number": "MUN-2002",
            "name": "AI Workflow Reliability Advisory",
            "department": "Regional Technology Cooperative",
            "posted_at": "2026-07-08",
            "deadline": "2026-09-01",
            "remote_policy": "remote",
            "engagement_model": "consulting",
            "budget_floor": 100_000,
            "budget_ceiling": 210_000,
            "required_skills": "ai|observability|python",
            "updated_at": "2026-07-08T14:00:00-05:00",
        },
        {
            "solicitation_number": "MUN-INVALID",
            "name": "Intentionally inverted fixture window",
            "department": "Fixture Quality Office",
            "posted_at": "2026-09-10",
            "deadline": "2026-09-01",
            "remote_policy": "remote",
            "engagement_model": "contract",
            "budget_floor": 20_000,
            "budget_ceiling": 40_000,
            "required_skills": "testing|data-quality",
            "updated_at": "2026-07-09T14:00:00-05:00",
        },
    )
    return SourceFixture(
        version="synthetic-v1",
        seed=seed,
        batches={"federal": federal, "municipal": municipal},
    )

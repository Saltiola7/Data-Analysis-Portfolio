"""Deterministic synthetic inputs for local, CI, and browser demos."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Final

import pandas as pd

from .models import SyntheticFixture

GENERATOR_VERSION: Final = "wellness-synthetic-v1"


def generate_synthetic_fixture(seed: int = 2026) -> SyntheticFixture:
    """Generate bounded synthetic inputs without files, networks, or private data."""

    rng = random.Random(seed)
    participant_count = 6
    day_count = 5
    first_day = date(2026, 2, 1)

    participants = [
        {
            "participant_id": f"P-{number:03d}",
            "cohort": ("alpha", "beta", "gamma")[(number - 1) % 3],
            "joined_on": (first_day - timedelta(days=7 + number)).isoformat(),
        }
        for number in range(1, participant_count + 1)
    ]

    duration_units = ("min", "minutes", "h", "hours")
    daily_signals: list[dict[str, object]] = []
    for number in range(1, participant_count + 1):
        participant_id = f"P-{number:03d}"
        for offset in range(day_count):
            sleep_minutes = rng.randrange(360, 541, 15)
            active_minutes = rng.randrange(15, 121, 5)
            sleep_unit = rng.choice(duration_units)
            active_unit = rng.choice(duration_units)
            daily_signals.append(
                {
                    "participant_id": participant_id,
                    "observed_on": (first_day + timedelta(days=offset)).isoformat(),
                    "sleep_value": (
                        sleep_minutes / 60 if sleep_unit in {"h", "hours"} else sleep_minutes
                    ),
                    "sleep_unit": sleep_unit,
                    "active_value": (
                        active_minutes / 60 if active_unit in {"h", "hours"} else active_minutes
                    ),
                    "active_unit": active_unit,
                    "pulse_bpm": rng.randrange(52, 91),
                }
            )

    daily_signals.extend(
        [
            {
                "participant_id": "P-999",
                "observed_on": (first_day + timedelta(days=day_count)).isoformat(),
                "sleep_value": 7.5,
                "sleep_unit": "h",
                "active_value": 30,
                "active_unit": "min",
                "pulse_bpm": 65,
            },
            {
                "participant_id": "P-001",
                "observed_on": (first_day + timedelta(days=day_count + 1)).isoformat(),
                "sleep_value": 8,
                "sleep_unit": "unsupported",
                "active_value": 30,
                "active_unit": "min",
                "pulse_bpm": 65,
            },
        ]
    )

    dose_units = ("mcg", "ug", "mg", "g")
    interventions: list[dict[str, object]] = []
    event_number = 1
    for participant_number in range(1, participant_count + 1):
        participant_id = f"P-{participant_number:03d}"
        for offset in range(day_count):
            event_count = rng.randrange(0, 3)
            for event_index in range(event_count):
                unit = rng.choice(dose_units)
                milligrams = rng.choice((0.25, 0.5, 1.0, 2.0))
                if unit in {"mcg", "ug"}:
                    source_value = milligrams * 1000
                elif unit == "g":
                    source_value = milligrams / 1000
                else:
                    source_value = milligrams
                interventions.append(
                    {
                        "intervention_id": f"I-{event_number:04d}",
                        "participant_id": participant_id,
                        "occurred_on": (first_day + timedelta(days=offset)).isoformat(),
                        "intervention": f"routine-{event_index + 1}",
                        "dose_value": source_value,
                        "dose_unit": unit,
                    }
                )
                event_number += 1

    interventions.append(
        {
            "intervention_id": f"I-{event_number:04d}",
            "participant_id": "P-999",
            "occurred_on": first_day.isoformat(),
            "intervention": "routine-unknown",
            "dose_value": 1,
            "dose_unit": "mg",
        }
    )

    rng.shuffle(participants)
    rng.shuffle(daily_signals)
    rng.shuffle(interventions)

    return SyntheticFixture(
        participants=pd.DataFrame(participants),
        daily_signals=pd.DataFrame(daily_signals),
        interventions=pd.DataFrame(interventions),
        seed=seed,
        generator_version=GENERATOR_VERSION,
    )

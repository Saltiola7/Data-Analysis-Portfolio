"""Unit normalization with stable, public failure semantics."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Final

from .models import NormalizationError

DURATION_MULTIPLIERS: Final[dict[str, Decimal]] = {
    "minute": Decimal(1),
    "minutes": Decimal(1),
    "min": Decimal(1),
    "hour": Decimal(60),
    "hours": Decimal(60),
    "h": Decimal(60),
}

DOSE_MULTIPLIERS: Final[dict[str, Decimal]] = {
    "mcg": Decimal("0.001"),
    "ug": Decimal("0.001"),
    "mg": Decimal(1),
    "g": Decimal(1000),
}


def _nonnegative_decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise NormalizationError("invalid_numeric_value", "value must be a finite number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise NormalizationError(
            "invalid_numeric_value", "value must be a finite number"
        ) from None
    if not number.is_finite():
        raise NormalizationError("invalid_numeric_value", "value must be a finite number")
    if number < 0:
        raise NormalizationError("negative_value", "value must be nonnegative")
    return number


def _normalized_unit(unit: object) -> str:
    if not isinstance(unit, str):
        return ""
    return unit.strip().lower()


def normalize_duration(value: object, unit: object) -> float:
    """Normalize a nonnegative duration to minutes."""

    normalized_unit = _normalized_unit(unit)
    multiplier = DURATION_MULTIPLIERS.get(normalized_unit)
    if multiplier is None:
        raise NormalizationError("unsupported_duration_unit", "unsupported duration unit")
    return float(_nonnegative_decimal(value) * multiplier)


def normalize_dose_mg(value: object, unit: object) -> float:
    """Normalize a nonnegative dose to milligrams."""

    normalized_unit = _normalized_unit(unit)
    multiplier = DOSE_MULTIPLIERS.get(normalized_unit)
    if multiplier is None:
        raise NormalizationError("unsupported_dose_unit", "unsupported dose unit")
    return float(_nonnegative_decimal(value) * multiplier)


def normalize_nonnegative_number(value: object) -> float:
    """Normalize an unscaled nonnegative numeric measurement."""

    return float(_nonnegative_decimal(value))

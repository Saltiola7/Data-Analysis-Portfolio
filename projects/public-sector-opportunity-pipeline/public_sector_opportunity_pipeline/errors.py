"""Controlled public errors for pipeline boundaries."""

from __future__ import annotations


class PipelineInputError(ValueError):
    """Input shape, volume, or state violates a pipeline contract."""


class TransientSourceError(RuntimeError):
    """A source operation may be retried safely."""


class PermanentSourceError(RuntimeError):
    """A source operation must stop without retry."""


class RetryExhaustedError(RuntimeError):
    """Bounded transient retries ended without a result."""

    def __init__(self, source: str, attempts: int) -> None:
        super().__init__(f"{source} failed after {attempts} attempts")
        self.source = source
        self.attempts = attempts


class RecordValidationError(ValueError):
    """Internal controlled dead-letter classification."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from src.core.contracts import ContractValidationError


@dataclass(frozen=True)
class ErrorClassification:
    retryable: bool
    reason: str


class RetryPolicy:
    def __init__(
        self,
        *,
        max_retry: int = 3,
        base_delay_seconds: float = 0.5,
        max_delay_seconds: float = 8.0,
        jitter_ratio: float = 0.2,
        seed: int | None = None,
    ) -> None:
        self.max_retry = max_retry
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.jitter_ratio = jitter_ratio
        self._random = random.Random(seed)

    def next_delay(self, attempt: int) -> float:
        exponential = min(self.base_delay_seconds * (2 ** max(0, attempt - 1)), self.max_delay_seconds)
        jitter_window = exponential * self.jitter_ratio
        jitter = self._random.uniform(0.0, jitter_window)
        return round(exponential + jitter, 6)

    async def sleep(self, attempt: int) -> float:
        delay = self.next_delay(attempt)
        await asyncio.sleep(delay)
        return delay


def classify_error(exc: Exception) -> ErrorClassification:
    response = getattr(exc, "response", None)
    status_code = getattr(exc, "status_code", None) or getattr(response, "status_code", None)
    if status_code in {401, 403}:
        return ErrorClassification(retryable=False, reason="authentication_or_authorization_error")
    if status_code == 429:
        return ErrorClassification(retryable=True, reason="rate_limited")
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return ErrorClassification(retryable=True, reason="timeout")
    if isinstance(exc, (ValidationError, ValueError, PermissionError)):
        return ErrorClassification(retryable=False, reason="invalid_payload_or_policy")
    if isinstance(exc, ContractValidationError):
        return ErrorClassification(retryable=False, reason="contract_validation_error")
    if isinstance(exc, OSError):
        return ErrorClassification(retryable=True, reason="transient_network_or_io")
    if status_code is not None and 500 <= status_code < 600:
        return ErrorClassification(retryable=True, reason="provider_server_error")
    return ErrorClassification(retryable=False, reason="non_retryable_default")

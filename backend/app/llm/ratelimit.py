"""
Token-bucket rate limiter + concurrency semaphore for LLM providers.

Limits are read from settings at construction time:
  - rpm  (requests per minute) → token refill rate
  - concurrency → max simultaneous in-flight calls

Thread-safe (uses threading.Lock + threading.Semaphore).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """Token-bucket rate limiter (requests per minute)."""

    def __init__(self, rpm: int, concurrency: int, provider: str = ""):
        self._provider = provider
        self._rpm = rpm
        self._tokens = float(rpm)
        self._max_tokens = float(rpm)
        self._refill_rate = rpm / 60.0   # tokens per second
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._sem = threading.Semaphore(concurrency)

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_tokens, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

    def acquire(self, timeout: float = 60.0) -> bool:
        """Block until a token is available (or timeout). Returns True on success."""
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(0.1, remaining))

    def call(self, fn: Callable[[], T], timeout: float = 60.0) -> T:
        """Acquire rate-limit token + concurrency slot, then call *fn*."""
        if not self.acquire(timeout=timeout):
            from app.core.errors import QuotaExceededError
            raise QuotaExceededError(
                f"Rate limit timeout for provider '{self._provider}'"
            )
        with self._sem:
            return fn()

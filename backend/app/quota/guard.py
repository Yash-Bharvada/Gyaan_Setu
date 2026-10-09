"""
Budget guard for metered providers.

Usage::

    guard = BudgetGuard("sarvam", unit="calls", hard_cap=100)
    guard.check()          # raises QuotaExceededError if over cap
    guard.record(1, 0.05)  # record usage and cost
"""
from __future__ import annotations

from app.core.errors import QuotaExceededError
from app.quota.ledger import UsageLedger


class BudgetGuard:
    """Hard-cap guard around a UsageLedger counter."""

    def __init__(self, provider: str, unit: str, hard_cap: float):
        self._provider = provider
        self._unit = unit
        self._cap = hard_cap
        self._ledger = UsageLedger.instance()

    def remaining(self) -> float:
        return self._cap - self._ledger.total(self._provider, self._unit)

    def is_over(self) -> bool:
        return self.remaining() <= 0

    def check(self) -> None:
        """Raise QuotaExceededError if the hard cap has been reached."""
        if self.is_over():
            raise QuotaExceededError(
                f"Budget cap for {self._provider}/{self._unit} reached "
                f"(cap={self._cap}). Falling back to local alternative."
            )

    def record(self, amount: float, est_cost: float = 0.0) -> None:
        self._ledger.record(self._provider, self._unit, amount, est_cost)


def get_freeocr_guard() -> BudgetGuard:
    from app.core.config import settings
    return BudgetGuard("freeocr.ai", "calls", settings.FREEOCR_MAX_CALLS)


def get_sarvam_guard() -> BudgetGuard:
    from app.core.config import settings
    return BudgetGuard("sarvam", "inr", settings.SARVAM_BUDGET_INR)


def get_elevenlabs_guard() -> BudgetGuard:
    # Free tier character limit: 10,000 characters per month hard cap
    return BudgetGuard("elevenlabs", "characters", 10000.0)

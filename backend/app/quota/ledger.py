"""
Persisted usage ledger for metered providers (freeocr.ai, Sarvam AI).

Each call is written to the ``usage_ledger`` table. Totals are queried from
SQLite (not kept only in memory) so a restart doesn't reset the counter.

Usage::

    from app.quota.ledger import UsageLedger
    ledger = UsageLedger.instance()
    ledger.record("freeocr.ai", "calls", 1, est_cost=0.002)
    total_calls = ledger.total("freeocr.ai", "calls")
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Optional


class UsageLedger:
    """Singleton ledger backed by SQLAlchemy (re-uses the app DB session)."""

    _instance: "UsageLedger | None" = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls) -> "UsageLedger":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def record(
        self,
        provider: str,
        unit: str,
        amount: float,
        est_cost: float = 0.0,
    ) -> None:
        """Write one ledger entry."""
        from app.core.db import SessionLocal
        from app.models import UsageLedgerEntry

        with SessionLocal() as db:
            entry = UsageLedgerEntry(
                provider=provider,
                unit=unit,
                amount=amount,
                est_cost=est_cost,
                ts=datetime.utcnow(),
            )
            db.add(entry)
            db.commit()

    def total(self, provider: str, unit: str) -> float:
        """Sum of *amount* for (provider, unit) across all time."""
        from sqlalchemy import func, select
        from app.core.db import SessionLocal
        from app.models import UsageLedgerEntry

        with SessionLocal() as db:
            result = db.execute(
                select(func.sum(UsageLedgerEntry.amount)).where(
                    UsageLedgerEntry.provider == provider,
                    UsageLedgerEntry.unit == unit,
                )
            ).scalar()
            return float(result or 0.0)

    def totals_by_provider(self) -> dict:
        """Return nested {provider: {unit: total, est_cost: total}} dict."""
        from sqlalchemy import func, select
        from app.core.db import SessionLocal
        from app.models import UsageLedgerEntry

        with SessionLocal() as db:
            rows = db.execute(
                select(
                    UsageLedgerEntry.provider,
                    UsageLedgerEntry.unit,
                    func.sum(UsageLedgerEntry.amount).label("total_amount"),
                    func.sum(UsageLedgerEntry.est_cost).label("total_cost"),
                ).group_by(UsageLedgerEntry.provider, UsageLedgerEntry.unit)
            ).all()

        out: dict = {}
        for row in rows:
            p = out.setdefault(row.provider, {})
            p[row.unit] = {"amount": row.total_amount, "est_cost": row.total_cost}
        return out

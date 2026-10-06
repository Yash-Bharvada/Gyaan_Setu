"""Forgetting Curve & Knowledge Decay module.

Models memory retention decay over time using exponential / power-law retention curves:
    $R(t) = e^{-t / S}$
where $S$ is stability in days and $t$ is days elapsed since last review.
"""
from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Mastery, Student, Topic


class ForgettingModel:
    @staticmethod
    def calculate_retrievability(stability_days: float, elapsed_days: float) -> float:
        """Calculate retrievability probability R in [0, 1]."""
        s = max(0.5, stability_days)
        t = max(0.0, elapsed_days)
        r = math.exp(-t / s)
        return round(float(max(0.01, min(1.0, r))), 3)

    @staticmethod
    def get_decayed_mastery(db: Session, student_id: int) -> List[Dict[str, Any]]:
        """Compute retention retrievability and decay risk for all student topics."""
        student = db.get(Student, student_id)
        if not student:
            return []

        now = datetime.utcnow()
        topics = db.query(Topic).all()
        masteries = {m.topic_id: m for m in student.mastery}

        results = []
        for t in topics:
            m = masteries.get(t.id)
            if m:
                elapsed_days = (now - m.last_updated).total_seconds() / 86400.0 if m.last_updated else 1.0
                stability = m.stability_days or 1.0
                retrievability = ForgettingModel.calculate_retrievability(stability, elapsed_days)
                effective_p = round(m.p_known * retrievability, 3)
            else:
                elapsed_days = 0.0
                stability = 1.0
                retrievability = 1.0
                effective_p = 0.30

            needs_urgent_review = effective_p < 0.60 or retrievability < 0.65

            results.append({
                "topic_id": t.id,
                "topic_name": t.name,
                "stability_days": stability,
                "elapsed_days": round(elapsed_days, 1),
                "retrievability": retrievability,
                "stored_p_known": m.p_known if m else 0.30,
                "effective_p_known": effective_p,
                "needs_urgent_review": needs_urgent_review,
            })

        return results

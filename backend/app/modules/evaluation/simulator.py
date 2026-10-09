"""Learner Trajectory Simulation module.

Simulates synthetic student learning paths across diverse learner personas
to validate BKT convergence, adaptive quiz effectiveness, and spaced scheduling.
"""
from __future__ import annotations

import json
import logging
import random
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import EvalRun, Topic
from app.modules.learner.bkt import BKTEngine, BKTParams

logger = logging.getLogger(__name__)


class StudentSimulator:
    PERSONAS = {
        "fast_learner": {"p_init": 0.40, "p_transit": 0.35, "p_guess": 0.25, "p_slip": 0.05, "decay_rate": 0.05},
        "average_learner": {"p_init": 0.25, "p_transit": 0.18, "p_guess": 0.20, "p_slip": 0.10, "decay_rate": 0.10},
        "struggling_learner": {"p_init": 0.15, "p_transit": 0.08, "p_guess": 0.15, "p_slip": 0.15, "decay_rate": 0.20},
    }

    @staticmethod
    def simulate_trajectory(
        db: Session,
        persona: str = "average_learner",
        days: int = 7,
        sessions_per_day: int = 2,
    ) -> Dict[str, Any]:
        """Simulate learning trajectory over N days."""
        cfg = StudentSimulator.PERSONAS.get(persona, StudentSimulator.PERSONAS["average_learner"])
        params = BKTParams(
            p_init=cfg["p_init"],
            p_transit=cfg["p_transit"],
            p_guess=cfg["p_guess"],
            p_slip=cfg["p_slip"],
        )

        topics = db.query(Topic).all()
        topic_names = [t.name for t in topics] if topics else ["Fundamentals", "Mechanisms", "Applications"]

        # Initial knowledge state per topic
        knowledge_state = {t: cfg["p_init"] for t in topic_names}
        history = []

        for day in range(1, days + 1):
            day_log = {"day": day, "sessions": []}

            for session_num in range(1, sessions_per_day + 1):
                # Pick 2 topics to practice
                active_topics = random.sample(topic_names, min(2, len(topic_names)))
                session_updates = {}

                for t in active_topics:
                    current_p = knowledge_state[t]
                    # Student probability of answering correctly: P(correct) = P(L)*(1-S) + (1-P(L))*G
                    prob_correct = (current_p * (1.0 - params.p_slip)) + ((1.0 - current_p) * params.p_guess)
                    is_correct = random.random() < prob_correct

                    # Update BKT
                    new_p = BKTEngine.update(current_p, correct=is_correct, params=params)
                    knowledge_state[t] = new_p
                    session_updates[t] = {
                        "is_correct": is_correct,
                        "p_known": new_p,
                    }

                day_log["sessions"].append(session_updates)

            # Apply overnight forgetting decay
            for t in topic_names:
                decay = cfg["decay_rate"] * 0.1
                knowledge_state[t] = max(0.05, round(knowledge_state[t] * (1.0 - decay), 4))

            day_log["end_of_day_mastery"] = dict(knowledge_state)
            history.append(day_log)

        final_avg_mastery = round(sum(knowledge_state.values()) / max(1, len(knowledge_state)), 3)

        return {
            "persona": persona,
            "days_simulated": days,
            "final_mastery_average": final_avg_mastery,
            "trajectory": history,
        }

    @staticmethod
    def run_and_save_simulation(
        db: Session,
        persona: str = "average_learner",
        days: int = 7,
    ) -> EvalRun:
        """Run simulation and record evaluation run in DB."""
        sim_data = StudentSimulator.simulate_trajectory(db, persona=persona, days=days)
        eval_run = EvalRun(
            kind="simulation",
            metrics=json.dumps(sim_data),
        )
        db.add(eval_run)
        db.commit()
        db.refresh(eval_run)
        return eval_run

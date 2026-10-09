"""Cold-start Diagnostic Module.

Generates diagnostic assessments to measure student baseline knowledge,
initializing topic priors without requiring full quiz history.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Mastery, Question, Student, Topic

logger = logging.getLogger(__name__)


class DiagnosticCalibrator:
    @staticmethod
    def get_diagnostic_questions(db: Session, max_questions: int = 5) -> List[Question]:
        """Select representative questions across distinct topics for diagnostic evaluation."""
        topics = db.query(Topic).all()
        selected_questions: List[Question] = []
        used_topic_ids = set()

        for t in topics:
            q = db.query(Question).filter(Question.topic_id == t.id).first()
            if q and t.id not in used_topic_ids:
                selected_questions.append(q)
                used_topic_ids.add(t.id)
                if len(selected_questions) >= max_questions:
                    break

        if len(selected_questions) < max_questions:
            remaining = db.query(Question).filter(~Question.id.in_([q.id for q in selected_questions])).limit(max_questions - len(selected_questions)).all()
            selected_questions.extend(remaining)

        return selected_questions

    @staticmethod
    def calibrate_student_priors(
        db: Session,
        student_id: int,
        results: List[Dict[str, Any]],  # [{"topic_id": int, "correct": bool}]
    ) -> Dict[str, float]:
        """Calibrate initial p_known values for topics based on diagnostic results."""
        student = db.get(Student, student_id)
        if not student:
            return {}

        mastery_map = {}
        for res in results:
            t_id = res.get("topic_id")
            correct = bool(res.get("correct"))

            if t_id:
                mastery = db.query(Mastery).filter(
                    Mastery.student_id == student_id,
                    Mastery.topic_id == t_id,
                ).first()

                # High baseline if correct, low baseline if incorrect
                initial_p = 0.70 if correct else 0.15

                if not mastery:
                    mastery = Mastery(
                        student_id=student_id,
                        topic_id=t_id,
                        p_known=initial_p,
                        n_attempts=1,
                    )
                    db.add(mastery)
                else:
                    mastery.p_known = initial_p
                    mastery.n_attempts += 1

                mastery_map[t_id] = initial_p

        db.commit()
        return mastery_map

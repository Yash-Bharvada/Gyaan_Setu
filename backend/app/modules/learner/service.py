"""Learner Service.

Manages student profiles, BKT knowledge state updates, mastery decay, and diagnostic pipelines.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Mastery, Student, Topic
from app.modules.learner.bkt import BKTEngine, BKTParams
from app.modules.learner.diagnostic import DiagnosticCalibrator


class LearnerService:
    @staticmethod
    def create_student(
        db: Session,
        name: str,
        lang: str = "en",
        exam_date: Optional[datetime] = None,
        daily_minutes: Optional[int] = 30,
        goals: Optional[str] = None,
    ) -> Student:
        student = Student(
            name=name,
            lang=lang,
            exam_date=exam_date,
            daily_minutes=daily_minutes,
            goals=goals,
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def get_student(db: Session, student_id: int) -> Student:
        student = db.get(Student, student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        return student

    @staticmethod
    def record_attempt(
        db: Session,
        student_id: int,
        topic_id: int,
        correct: bool,
    ) -> Mastery:
        """Update student's BKT knowledge state for a topic after an attempt."""
        student = db.get(Student, student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")

        mastery = db.query(Mastery).filter(
            Mastery.student_id == student_id,
            Mastery.topic_id == topic_id,
        ).first()

        if not mastery:
            mastery = Mastery(
                student_id=student_id,
                topic_id=topic_id,
                p_known=0.30,
                stability_days=1.0,
                n_attempts=0,
            )
            db.add(mastery)

        # Apply BKT update
        new_p = BKTEngine.update(mastery.p_known, correct=correct)
        new_stability = BKTEngine.update_stability(mastery.stability_days, correct=correct, p_known=new_p)

        mastery.p_known = new_p
        mastery.stability_days = new_stability
        mastery.n_attempts += 1
        mastery.last_updated = datetime.utcnow()

        db.commit()
        db.refresh(mastery)
        return mastery

    @staticmethod
    def get_mastery_overview(db: Session, student_id: int) -> List[Dict[str, Any]]:
        """Get full mastery status for all topics for a student."""
        student = db.get(Student, student_id)
        if not student:
            if student_id == 1:
                student = Student(
                    id=1,
                    name="Alex Chen",
                    lang="en",
                    daily_minutes=30,
                )
                db.add(student)
                db.commit()
                db.refresh(student)
            else:
                raise NotFoundError(f"Student {student_id} not found")

        topics = db.query(Topic).all()
        masteries = {m.topic_id: m for m in student.mastery}

        result = []
        for t in topics:
            m = masteries.get(t.id)
            p_known = m.p_known if m else 0.30
            stability = m.stability_days if m else 1.0
            n_attempts = m.n_attempts if m else 0

            status = "mastered" if p_known >= 0.85 else ("in_progress" if p_known >= 0.50 else "needs_review")

            result.append({
                "topic_id": t.id,
                "topic_name": t.name,
                "level": t.level,
                "p_known": p_known,
                "stability_days": stability,
                "n_attempts": n_attempts,
                "status": status,
            })
        return result

"""Learner API Router.

Endpoints for student profile management, BKT mastery monitoring, and diagnostic tests.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.learner.diagnostic import DiagnosticCalibrator
from app.modules.learner.service import LearnerService

router = APIRouter(prefix="/learner", tags=["Learner Model"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    name: str
    lang: Optional[str] = "en"
    exam_date: Optional[datetime] = None
    daily_minutes: Optional[int] = 30
    goals: Optional[str] = None


class AttemptPayload(BaseModel):
    topic_id: int
    correct: bool


class DiagnosticItem(BaseModel):
    topic_id: int
    correct: bool


class DiagnosticPayload(BaseModel):
    results: List[DiagnosticItem]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/students", response_model=Dict[str, Any])
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    """Register a new student profile."""
    student = LearnerService.create_student(
        db=db,
        name=payload.name,
        lang=payload.lang or "en",
        exam_date=payload.exam_date,
        daily_minutes=payload.daily_minutes,
        goals=payload.goals,
    )
    return {
        "id": student.id,
        "name": student.name,
        "lang": student.lang,
        "daily_minutes": student.daily_minutes,
        "exam_date": student.exam_date,
    }


@router.get("/students/{student_id}", response_model=Dict[str, Any])
def get_student_profile(student_id: int, db: Session = Depends(get_db)):
    """Get student profile details."""
    student = LearnerService.get_student(db, student_id)
    return {
        "id": student.id,
        "name": student.name,
        "lang": student.lang,
        "daily_minutes": student.daily_minutes,
        "exam_date": student.exam_date,
        "goals": student.goals,
    }


@router.get("/students/{student_id}/mastery", response_model=List[Dict[str, Any]])
def get_student_mastery(student_id: int, db: Session = Depends(get_db)):
    """Get topic-by-topic BKT knowledge mastery states for a student."""
    return LearnerService.get_mastery_overview(db, student_id)


@router.post("/students/{student_id}/attempt", response_model=Dict[str, Any])
def record_topic_attempt(student_id: int, payload: AttemptPayload, db: Session = Depends(get_db)):
    """Record a learning attempt and update the student's BKT mastery state."""
    mastery = LearnerService.record_attempt(
        db=db,
        student_id=student_id,
        topic_id=payload.topic_id,
        correct=payload.correct,
    )
    return {
        "student_id": student_id,
        "topic_id": mastery.topic_id,
        "p_known": mastery.p_known,
        "stability_days": mastery.stability_days,
        "n_attempts": mastery.n_attempts,
    }


@router.get("/diagnostic/questions", response_model=List[Dict[str, Any]])
def get_diagnostic_questions(limit: int = 5, db: Session = Depends(get_db)):
    """Fetch diagnostic question set for cold-start evaluation."""
    questions = DiagnosticCalibrator.get_diagnostic_questions(db, max_questions=limit)
    return [
        {
            "id": q.id,
            "stem": q.stem,
            "type": q.type.value,
            "options": q.options,
            "topic_id": q.topic_id,
        }
        for q in questions
    ]


@router.post("/students/{student_id}/diagnostic", response_model=Dict[str, Any])
def submit_diagnostic(student_id: int, payload: DiagnosticPayload, db: Session = Depends(get_db)):
    """Submit diagnostic results to initialize baseline topic mastery priors."""
    raw_results = [{"topic_id": item.topic_id, "correct": item.correct} for item in payload.results]
    calibrated = DiagnosticCalibrator.calibrate_student_priors(db, student_id, raw_results)
    return {
        "status": "calibrated",
        "student_id": student_id,
        "calibrated_topics": calibrated,
    }

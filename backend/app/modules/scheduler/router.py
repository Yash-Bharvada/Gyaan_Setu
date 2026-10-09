"""Study Scheduler API Router.

Endpoints for generating and viewing personalized spaced revision calendars and forgetting decay.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import Schedule
from app.modules.scheduler.forgetting import ForgettingModel
from app.modules.scheduler.planner import StudyPlanner

router = APIRouter(prefix="/scheduler", tags=["Study Scheduler"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    student_id: int
    target_days: Optional[int] = None
    daily_minutes: Optional[int] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/plan", response_model=Dict[str, Any])
def generate_study_plan(
    payload: PlanRequest,
    db: Session = Depends(get_db),
):
    """Generate a multi-day personalized spaced revision schedule."""
    schedule = StudyPlanner.generate_schedule(
        db=db,
        student_id=payload.student_id,
        target_days=payload.target_days,
        daily_minutes=payload.daily_minutes,
    )
    return {
        "schedule_id": schedule.id,
        "student_id": schedule.student_id,
        "version": schedule.version,
        "generated_at": schedule.generated_at,
        "items": json.loads(schedule.items) if schedule.items else [],
    }


@router.get("/{student_id}", response_model=Dict[str, Any])
def get_student_schedule(student_id: int, db: Session = Depends(get_db)):
    """Retrieve the latest study schedule for a student."""
    schedule = db.query(Schedule).filter(Schedule.student_id == student_id).order_by(Schedule.generated_at.desc()).first()
    if not schedule:
        # Create a default schedule on request
        schedule = StudyPlanner.generate_schedule(db=db, student_id=student_id)

    return {
        "schedule_id": schedule.id,
        "student_id": schedule.student_id,
        "version": schedule.version,
        "items": json.loads(schedule.items) if schedule.items else [],
    }


@router.get("/{student_id}/decay", response_model=List[Dict[str, Any]])
def get_decay_status(student_id: int, db: Session = Depends(get_db)):
    """Get topic retrievability and decay risk modeled by the forgetting curve."""
    return ForgettingModel.get_decayed_mastery(db, student_id)

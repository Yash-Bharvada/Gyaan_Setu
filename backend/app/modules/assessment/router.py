"""Assessment API Router.

Endpoints for generating cross-model verified question banks, creating adaptive tests,
and grading student submissions with BKT mastery feedback.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_llm
from app.llm.base import LLMClient
from app.models import Assessment, AssessmentKind, Question
from app.modules.assessment.service import AssessmentService

router = APIRouter(prefix="/assessment", tags=["Assessment"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    topic_id: int
    count: Optional[int] = 2


class CreateQuizRequest(BaseModel):
    student_id: int
    kind: Optional[str] = "quiz"
    num_questions: Optional[int] = 5
    topic_ids: Optional[List[int]] = None


class AnswerSubmission(BaseModel):
    question_id: int
    response: str
    time_taken_secs: Optional[float] = 0.0


class SubmitQuizRequest(BaseModel):
    responses: List[AnswerSubmission]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=Dict[str, Any])
def generate_questions(
    payload: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Generate and cross-model verify assessment questions for a topic."""
    questions = AssessmentService.generate_questions_for_topic(
        db=db,
        topic_id=payload.topic_id,
        llm=llm,
        count=payload.count or 2,
    )
    return {
        "status": "generated",
        "topic_id": payload.topic_id,
        "count": len(questions),
        "questions": [
            {
                "id": q.id,
                "stem": q.stem,
                "type": q.type.value,
                "options": json.loads(q.options) if q.options else None,
                "verified": q.verified,
                "verification_strength": q.verification_strength,
            }
            for q in questions
        ],
    }


@router.post("/quiz", response_model=Dict[str, Any])
def create_adaptive_quiz(
    payload: CreateQuizRequest,
    db: Session = Depends(get_db),
):
    """Generate an adaptive quiz personalized to the student's mastery gaps."""
    kind = AssessmentKind(payload.kind) if payload.kind in [k.value for k in AssessmentKind] else AssessmentKind.quiz
    quiz = AssessmentService.create_quiz(
        db=db,
        student_id=payload.student_id,
        kind=kind,
        num_questions=payload.num_questions or 5,
        topic_ids=payload.topic_ids,
    )
    return {
        "assessment_id": quiz.id,
        "student_id": quiz.student_id,
        "status": quiz.status,
        "items": [
            {
                "question_id": it.question.id,
                "stem": it.question.stem,
                "type": it.question.type.value,
                "options": json.loads(it.question.options) if it.question.options else None,
                "answer_key": it.question.answer_key,
                "explanation": it.question.explanation,
                "distractor_rationales": json.loads(it.question.distractor_rationales) if it.question.distractor_rationales else {},
                "topic_id": it.question.topic_id,
                "topic_name": it.question.topic.name if it.question.topic else f"Topic #{it.question.topic_id}",
                "difficulty": it.question.difficulty,
            }
            for it in quiz.items
        ],
    }


@router.get("/{assessment_id}", response_model=Dict[str, Any])
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Fetch an assessment and its items/status."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return {
        "id": assessment.id,
        "student_id": assessment.student_id,
        "status": assessment.status,
        "score": assessment.score,
        "report": json.loads(assessment.report) if assessment.report else None,
        "items": [
            {
                "question_id": it.question.id,
                "stem": it.question.stem,
                "type": it.question.type.value,
                "options": json.loads(it.question.options) if it.question.options else None,
                "response": it.response,
                "score": it.score,
            }
            for it in assessment.items
        ],
    }


@router.post("/{assessment_id}/submit", response_model=Dict[str, Any])
def submit_assessment(
    assessment_id: int,
    payload: SubmitQuizRequest,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Submit answers for grading, calculate score, and update student BKT mastery."""
    raw_responses = [
        {"question_id": r.question_id, "response": r.response, "time_taken_secs": r.time_taken_secs}
        for r in payload.responses
    ]
    report = AssessmentService.submit_quiz(
        db=db,
        assessment_id=assessment_id,
        responses=raw_responses,
        llm=llm,
    )
    return report

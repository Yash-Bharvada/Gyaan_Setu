"""Revision API Router.

Endpoints for spaced repetition flashcards, slide takeaways, and audio brief scripts.
"""
from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_llm
from app.llm.base import LLMClient
from app.models import Flashcard
from app.modules.revision.brief import AudioBriefGenerator
from app.modules.revision.flashcards import FlashcardService
from app.modules.revision.slides import SlideSummarizer

router = APIRouter(prefix="/revision", tags=["Revision & Flashcards"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class GenerateFlashcardsRequest(BaseModel):
    student_id: int
    topic_id: int


class ReviewCardRequest(BaseModel):
    quality: int  # 0 to 5


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/flashcards/generate", response_model=Dict[str, Any])
def generate_flashcards(
    payload: GenerateFlashcardsRequest,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Generate grounded spaced repetition flashcards for a topic."""
    cards = FlashcardService.generate_flashcards(
        db=db,
        student_id=payload.student_id,
        topic_id=payload.topic_id,
        llm=llm,
    )
    return {
        "status": "generated",
        "student_id": payload.student_id,
        "topic_id": payload.topic_id,
        "count": len(cards),
        "cards": [
            {
                "id": c.id,
                "front": c.front,
                "back": c.back,
                "ease_factor": c.ease_factor,
                "interval_days": c.interval_days,
                "citation": json.loads(c.citation) if c.citation else None,
            }
            for c in cards
        ],
    }


@router.get("/flashcards", response_model=List[Dict[str, Any]])
def get_due_flashcards(student_id: int, db: Session = Depends(get_db)):
    """Fetch all flashcards due for review for a student."""
    now = datetime.utcnow()
    cards = db.query(Flashcard).filter(
        Flashcard.student_id == student_id,
        Flashcard.next_review_at <= now,
    ).all()

    if not cards:
        cards = db.query(Flashcard).filter(Flashcard.student_id == student_id).limit(10).all()

    return [
        {
            "id": c.id,
            "topic_id": c.topic_id,
            "front": c.front,
            "back": c.back,
            "ease_factor": c.ease_factor,
            "interval_days": c.interval_days,
            "n_reviews": c.n_reviews,
            "citation": json.loads(c.citation) if c.citation else None,
        }
        for c in cards
    ]


@router.post("/flashcards/{card_id}/review", response_model=Dict[str, Any])
def review_flashcard(
    card_id: int,
    payload: ReviewCardRequest,
    db: Session = Depends(get_db),
):
    """Record student flashcard review rating (0-5) and update SM-2 schedule."""
    card = FlashcardService.review_card(db, card_id=card_id, quality=payload.quality)
    return {
        "id": card.id,
        "ease_factor": card.ease_factor,
        "interval_days": card.interval_days,
        "n_reviews": card.n_reviews,
        "next_review_at": card.next_review_at,
    }


@router.get("/slides/{source_id}", response_model=Dict[str, Any])
def get_slide_summary(
    source_id: int,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Generate high-yield summary and key takeaways for a slide deck or chapter."""
    return SlideSummarizer.generate_summary_for_source(db, source_id, llm)


@router.get("/brief/{topic_id}", response_model=Dict[str, Any])
def get_audio_brief(
    topic_id: int,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Generate 2-minute revision audio brief script for a topic."""
    return AudioBriefGenerator.generate_brief(db, topic_id, llm)

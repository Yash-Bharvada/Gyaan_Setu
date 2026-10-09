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
def get_due_flashcards(
    student_id: int,
    limit: Optional[int] = 10,
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Fetch all flashcards due for review for a student."""
    query = db.query(Flashcard).filter(Flashcard.student_id == student_id)
    if topic_id:
        query = query.filter(Flashcard.topic_id == topic_id)

    cards = query.all()

    target_limit = limit or 10
    if len(cards) < target_limit:
        # Auto-generate fresh flashcards from curriculum topics until limit is met
        from app.models import Topic
        if topic_id:
            topics = db.query(Topic).filter(Topic.id == topic_id).all()
        else:
            topics = db.query(Topic).all()

        for t in topics:
            if len(cards) >= target_limit:
                break
            try:
                FlashcardService.generate_flashcards(db, student_id, t.id, llm, count=3)
                q = db.query(Flashcard).filter(Flashcard.student_id == student_id)
                if topic_id:
                    q = q.filter(Flashcard.topic_id == topic_id)
                cards = q.all()
            except Exception:
                pass

        # If a single narrow topic has fewer cards, top up with other curriculum flashcards
        if len(cards) < target_limit and topic_id:
            extra = db.query(Flashcard).filter(Flashcard.student_id == student_id, Flashcard.topic_id != topic_id).all()
            cards.extend(extra[:target_limit - len(cards)])

    if limit and limit > 0:
        cards = cards[:limit]

    return [
        {
            "id": c.id,
            "topic_id": c.topic_id,
            "topic_name": c.topic.name if c.topic else f"Topic #{c.topic_id}",
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
    mode: Optional[str] = "summary",
    language: Optional[str] = "en",
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    """Generate 2-minute revision audio brief or multi-host podcast script for a topic."""
    return AudioBriefGenerator.generate_brief(
        db, topic_id, llm, mode=mode or "summary", language=language or "en"
    )


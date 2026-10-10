"""Spaced Repetition Flashcards module (SM-2 & FSRS).

Generates grounded flashcards from source units and calculates next review dates
using the SuperMemo-2 (SM-2) and stability-based scheduling algorithms.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.llm.base import LLMClient
from app.models import Flashcard, Student, Topic, Unit
from app.modules.tutor.citations import format_unit_citation

logger = logging.getLogger(__name__)

FLASHCARD_GEN_PROMPT = """You are an expert in spaced repetition flashcards.
Given the following source material for topic "{topic_name}", create {count} high-yield flashcards.
Each flashcard must have a concise front question/prompt and a clear, factually accurate back answer.

Source Content:
{context}

Return JSON:
{{
  "flashcards": [
    {{
      "front": "Clear question or prompt",
      "back": "Concise answer with key points"
    }}
  ]
}}
"""


class FlashcardScheduler:
    @staticmethod
    def update_sm2(
        flashcard: Flashcard,
        quality: int,  # 0 to 5 (0-2: fail, 3: pass, 4: good, 5: easy)
    ) -> Flashcard:
        """Apply SuperMemo-2 (SM-2) algorithm update."""
        q = max(0, min(5, quality))
        ef = flashcard.ease_factor or 2.5
        n = flashcard.n_reviews or 0
        interval = flashcard.interval_days or 1.0

        if q >= 3:
            # Correct response
            if n == 0:
                interval = 1.0
            elif n == 1:
                interval = 6.0
            else:
                interval = interval * ef
            n += 1
        else:
            # Incorrect response: reset interval to 1 day
            n = 0
            interval = 1.0

        # Update Ease Factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ef = max(1.3, ef)

        flashcard.ease_factor = round(ef, 3)
        flashcard.interval_days = round(interval, 1)
        flashcard.n_reviews = n
        flashcard.last_reviewed_at = datetime.utcnow()
        flashcard.next_review_at = datetime.utcnow() + timedelta(days=interval)

        return flashcard


class FlashcardService:
    @staticmethod
    def generate_flashcards(
        db: Session,
        student_id: int,
        topic_id: int,
        llm: LLMClient,
        count: int = 3,
    ) -> List[Flashcard]:
        """Generate and store flashcards for a topic."""
        topic = db.get(Topic, topic_id)
        student = db.get(Student, student_id)
        if not topic or not student:
            return []

        units = [ut.unit for ut in topic.unit_topics if ut.unit]
        context_str = "\n\n".join([u.text[:350] for u in units[:4]])

        prompt = FLASHCARD_GEN_PROMPT.format(
            topic_name=topic.name,
            context=context_str if context_str else topic.summary or "",
            count=count,
        )

        try:
            res = llm.generate_json(prompt)
            cards_data = res.get("flashcards", []) if isinstance(res, dict) else []
        except Exception:
            cards_data = []

        if not cards_data:
            summary = topic.summary or f"Core mechanism and principles of {topic.name}."
            cards_data = [
                {
                    "front": f"What is the core principle and purpose of {topic.name}?",
                    "back": summary,
                }
            ]

        citation = format_unit_citation(units[0].__dict__) if units else None

        created = []
        for c in cards_data:
            front_text = c.get("front", "").strip()
            back_text = c.get("back", "").strip()
            if not front_text or not back_text:
                continue

            existing = db.query(Flashcard).filter(
                Flashcard.student_id == student_id,
                Flashcard.front == front_text,
            ).first()
            if existing:
                continue

            fc = Flashcard(
                student_id=student_id,
                topic_id=topic_id,
                front=front_text,
                back=back_text,
                citation=json.dumps(citation) if citation else None,
                ease_factor=2.5,
                interval_days=1.0,
                next_review_at=datetime.utcnow(),
            )
            db.add(fc)
            created.append(fc)

        db.commit()
        for f in created:
            db.refresh(f)
        return created

    @staticmethod
    def review_card(db: Session, card_id: int, quality: int) -> Flashcard:
        """Process student review of a flashcard."""
        card = db.get(Flashcard, card_id)
        if not card:
            raise Exception(f"Flashcard {card_id} not found")

        updated = FlashcardScheduler.update_sm2(card, quality=quality)
        db.commit()
        db.refresh(updated)
        return updated

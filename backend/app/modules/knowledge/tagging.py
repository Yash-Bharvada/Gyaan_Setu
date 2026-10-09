"""Concept Tagging module.

Maps content units to topics and concepts using embedding cosine similarity and LLM alignment.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.llm.base import LLMClient
from app.models import Topic, Unit, UnitTopic

logger = logging.getLogger(__name__)


def cosine_sim(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class ConceptTagger:
    @staticmethod
    def tag_units_to_topics(
        db: Session,
        llm: LLMClient,
        threshold: float = 0.35,
    ) -> int:
        """Tag all untagged units to appropriate topics based on embedding similarity."""
        units = db.query(Unit).all()
        topics = db.query(Topic).all()

        if not units or not topics:
            return 0

        # Generate embeddings for topics
        topic_texts = [f"{t.name}: {t.summary or ''}" for t in topics]
        topic_embeddings = llm.embed(topic_texts)

        # Generate embeddings for units
        unit_texts = [u.text[:400] for u in units]
        unit_embeddings = llm.embed(unit_texts)

        tagged_count = 0

        for u_idx, unit in enumerate(units):
            u_emb = unit_embeddings[u_idx]
            best_topic_id = None
            best_score = -1.0

            tagged_topic_ids = set()
            for t_idx, topic in enumerate(topics):
                t_emb = topic_embeddings[t_idx]
                sim = cosine_sim(u_emb, t_emb)

                if sim >= threshold:
                    existing = db.query(UnitTopic).filter(
                        UnitTopic.unit_id == unit.id,
                        UnitTopic.topic_id == topic.id,
                    ).first()

                    if not existing and topic.id not in tagged_topic_ids:
                        ut = UnitTopic(
                            unit_id=unit.id,
                            topic_id=topic.id,
                            confidence=round(float(sim), 4),
                            method="embedding",
                        )
                        db.add(ut)
                        tagged_topic_ids.add(topic.id)
                        tagged_count += 1

                if sim > best_score:
                    best_score = sim
                    best_topic_id = topic.id

            # Ensure every unit has at least its best matching topic
            if best_topic_id is not None and best_topic_id not in tagged_topic_ids:
                existing = db.query(UnitTopic).filter(
                    UnitTopic.unit_id == unit.id,
                    UnitTopic.topic_id == best_topic_id,
                ).first()
                if not existing:
                    ut = UnitTopic(
                        unit_id=unit.id,
                        topic_id=best_topic_id,
                        confidence=round(float(max(0.4, best_score)), 4),
                        method="embedding",
                    )
                    db.add(ut)
                    tagged_topic_ids.add(best_topic_id)
                    tagged_count += 1

        db.commit()
        return tagged_count

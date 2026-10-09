"""Revision Audio Brief module.

Creates punchy 2-minute audio review scripts structured for voice playback:
- Hook & Context
- Core Concept Breakdown
- Rapid-Fire Recall Check
- Mnemonic Wrap-up
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.llm.base import LLMClient
from app.models import Topic, Unit

logger = logging.getLogger(__name__)

AUDIO_BRIEF_PROMPT = """You are an engaging audio podcast tutor.
Write a crisp 2-minute audio brief script reviewing the topic "{topic_name}".

Source Context:
{context}

Format the script with these sections:
1. intro: Engaging 15-second hook.
2. core_concepts: Clear 60-second explanation with an intuitive real-world analogy.
3. rapid_check: A quick question for the listener to pause and think about.
4. mnemonic_wrap: A clever memory peg or takeaway.

Return JSON:
{{
  "topic": "{topic_name}",
  "estimated_duration_secs": 120,
  "sections": {{
    "intro": "Audio script intro...",
    "core_concepts": "Main conceptual review...",
    "rapid_check": "Quick question...",
    "mnemonic_wrap": "Memory takeaway..."
  }},
  "full_spoken_script": "Combined natural speech text for TTS engine."
}}
"""


class AudioBriefGenerator:
    @staticmethod
    def generate_brief(
        db: Session,
        topic_id: int,
        llm: LLMClient,
    ) -> Dict[str, Any]:
        """Generate audio revision brief script for a topic."""
        topic = db.get(Topic, topic_id)
        if not topic:
            return {"error": "Topic not found"}

        units = [ut.unit for ut in topic.unit_topics if ut.unit]
        context_str = "\n".join([u.text[:300] for u in units[:4]])

        prompt = AUDIO_BRIEF_PROMPT.format(
            topic_name=topic.name,
            context=context_str if context_str else topic.summary or "",
        )

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and "full_spoken_script" in res:
                return res
        except Exception as exc:
            logger.warning("Audio brief LLM fallback: %s", exc)

        spoken = (
            f"Welcome to your revision brief on {topic.name}. "
            f"Here is what you need to master: {topic.summary or 'The key foundational principles.'} "
            f"Remember the core rule: understand the fundamentals first before moving to complex applications."
        )

        return {
            "topic": topic.name,
            "estimated_duration_secs": 90,
            "sections": {
                "intro": f"Welcome to your revision brief on {topic.name}.",
                "core_concepts": topic.summary or "Fundamental mechanisms and definitions.",
                "rapid_check": f"What is the key mechanism governing {topic.name}?",
                "mnemonic_wrap": "Master the basics, solve step-by-step!",
            },
            "full_spoken_script": spoken,
        }

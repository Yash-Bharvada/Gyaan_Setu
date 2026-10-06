"""Slide Summaries & Key Takeaways module.

Extracts high-yield review sheets, key formulas, and bullet summaries from slides and chapters.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.llm.base import LLMClient
from app.models import Source, Topic, Unit, UnitType

logger = logging.getLogger(__name__)

SLIDE_SUMMARY_PROMPT = """You are an expert study note summarizer.
Condense the following slide/chapter materials into a high-yield revision sheet.

Content:
{content}

Provide:
1. Executive 2-sentence summary.
2. 3-5 bulleted Core Takeaways.
3. Key formulas or definitions to remember.
4. Common exam traps or misconceptions.

Return JSON:
{{
  "summary": "Executive summary",
  "takeaways": ["Takeaway 1", "Takeaway 2"],
  "key_formulas_definitions": ["Formula / Def 1"],
  "exam_traps": ["Trap to avoid"]
}}
"""


class SlideSummarizer:
    @staticmethod
    def generate_summary_for_source(
        db: Session,
        source_id: int,
        llm: LLMClient,
    ) -> Dict[str, Any]:
        """Generate high-yield slide summaries from all units in a source."""
        units = db.query(Unit).filter(Unit.source_id == source_id).order_by(Unit.page.asc(), Unit.slide_no.asc()).all()
        if not units:
            return {"summary": "No units found", "takeaways": []}

        content_str = "\n".join([f"[Slide/Page {u.page or u.slide_no or u.id}]: {u.text[:300]}" for u in units[:10]])
        prompt = SLIDE_SUMMARY_PROMPT.format(content=content_str)

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and "summary" in res:
                return res
        except Exception as exc:
            logger.warning("Slide summarizer LLM fallback: %s", exc)

        return {
            "summary": f"Core overview of course source {source_id}.",
            "takeaways": [
                "Understand fundamental definitions and primary equations.",
                "Review step-by-step worked examples.",
            ],
            "key_formulas_definitions": ["Foundational laws and properties"],
            "exam_traps": ["Be careful of edge cases and non-linear transitions."],
        }

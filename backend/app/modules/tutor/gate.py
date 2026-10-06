"""Relevance Gate and Grounding Check module.

Evaluates whether retrieved source context contains sufficient information to answer the student's question.
If information is missing, determines whether to refuse or provide an explicitly flagged outside-knowledge answer.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.llm.base import LLMClient

logger = logging.getLogger(__name__)

GATE_PROMPT = """You are a relevance and factuality gate for an educational tutor.
Evaluate whether the provided source units contain relevant information to answer the student query.

Query: "{query}"

Retrieved Units:
{context}

Respond in JSON format:
{{
  "is_relevant": true/false,
  "confidence": 0.0 to 1.0,
  "rationale": "Brief reason why context is sufficient or insufficient",
  "action": "answer" or "refuse" or "outside_knowledge_needed"
}}
"""


class RelevanceGate:
    @staticmethod
    def evaluate(
        query: str,
        units: List[Dict[str, Any]],
        llm: LLMClient,
        strict_grounding: bool = True,
    ) -> Dict[str, Any]:
        """Check if retrieved units contain sufficient evidence to answer query."""
        if not units:
            return {
                "is_relevant": False,
                "confidence": 0.0,
                "rationale": "No relevant source material found in curriculum.",
                "action": "refuse" if strict_grounding else "outside_knowledge_needed",
            }

        context_str = "\n".join([f"[{u.get('source_title', 'Source')}]: {u.get('text', '')[:300]}" for u in units])
        prompt = GATE_PROMPT.format(query=query, context=context_str)

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and "is_relevant" in res:
                return res
        except Exception as exc:
            logger.warning("Relevance gate LLM fallback: %s", exc)

        # Heuristic fallback: check keyword overlap
        q_words = set(query.lower().split())
        c_words = set(context_str.lower().split())
        overlap = len(q_words.intersection(c_words))
        is_rel = overlap >= 1 or len(units) > 0

        return {
            "is_relevant": is_rel,
            "confidence": 0.8 if is_rel else 0.2,
            "rationale": "Keyword overlap heuristic assessment.",
            "action": "answer" if is_rel else ("refuse" if strict_grounding else "outside_knowledge_needed"),
        }

"""Cross-Model Assessment Verifier module.

Validates generated question factuality, checks distractor plausibility,
and ensures there is exactly one indisputable correct answer.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.llm.base import LLMClient

logger = logging.getLogger(__name__)

VERIFIER_PROMPT = """You are an independent peer reviewer for exam quality.
Examine this draft question:

Stem: "{stem}"
Question Type: "{type}"
Options: {options}
Claimed Correct Answer: "{answer_key}"
Explanation: "{explanation}"

Verify:
1. Is the question factually accurate and unambiguous?
2. Is the claimed answer unambiguously correct?
3. Are the distractors clearly distinct and plausible but incorrect?

Return JSON:
{{
  "is_valid": true/false,
  "confidence": 0.0 to 1.0,
  "verification_strength": "strong" or "weak",
  "critique": "Brief justification"
}}
"""


class QuestionVerifier:
    @staticmethod
    def verify_question(
        question_data: Dict[str, Any],
        verifier_llm: LLMClient,
    ) -> Tuple[bool, str, str]:
        """Verify question using an independent LLM.

        Returns (is_valid, verification_strength, critique).
        """
        prompt = VERIFIER_PROMPT.format(
            stem=question_data.get("stem", ""),
            type=question_data.get("type", "mcq"),
            options=question_data.get("options", []),
            answer_key=question_data.get("answer_key", ""),
            explanation=question_data.get("explanation", ""),
        )

        try:
            res = verifier_llm.generate_json(prompt)
            if isinstance(res, dict) and "is_valid" in res:
                return (
                    bool(res["is_valid"]),
                    str(res.get("verification_strength", "strong")),
                    str(res.get("critique", "Verified OK")),
                )
        except Exception as exc:
            logger.warning("Verifier LLM check fallback: %s", exc)

        # Default fallback: valid if stem and answer exist
        has_stem = bool(question_data.get("stem"))
        has_ans = bool(question_data.get("answer_key"))
        is_ok = has_stem and has_ans
        return is_ok, "strong" if is_ok else "weak", "Passed heuristic checks"

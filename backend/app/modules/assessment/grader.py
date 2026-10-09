"""Assessment Grader module.

Grades student responses using exact matching for MCQs, numerical tolerance for math questions,
and rubric-based LLM evaluation for short-answer questions.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.llm.base import LLMClient
from app.models import Question, QuestionType

logger = logging.getLogger(__name__)

RUBRIC_GRADING_PROMPT = """You are a fair, precise academic grader.
Evaluate the student's response against the question, answer key, and explanation.

Question: "{stem}"
Expected Answer / Key: "{answer_key}"
Reference Explanation: "{explanation}"
Student Response: "{student_response}"

Grade on a scale from 0.0 to 1.0 (1.0 = completely correct, 0.5 = partially correct, 0.0 = completely incorrect).
Provide constructive pedagogical feedback.

Return JSON:
{{
  "score": 0.0 to 1.0,
  "is_correct": true/false,
  "feedback": "Detailed constructive feedback explaining what was correct or missing.",
  "strengths": ["Key point mentioned"],
  "weaknesses": ["Key concept missed"]
}}
"""


class AssessmentGrader:
    @staticmethod
    def grade_item(
        question: Question,
        student_response: str,
        llm: LLMClient,
    ) -> Dict[str, Any]:
        """Grade a single question response."""
        resp_clean = (student_response or "").strip()
        ans_clean = (question.answer_key or "").strip()

        # 1. Multiple Choice Question
        if question.type == QuestionType.mcq:
            is_correct = resp_clean.lower() == ans_clean.lower() or (
                len(resp_clean) == 1 and ans_clean.lower().startswith(resp_clean.lower())
            )
            score = 1.0 if is_correct else 0.0
            feedback = (
                "Correct! Excellent grasp of the concept."
                if is_correct
                else f"Incorrect. The correct answer was: {question.answer_key}. {question.explanation or ''}"
            )
            return {
                "score": score,
                "is_correct": is_correct,
                "feedback": feedback,
            }

        # 2. Numerical Question
        elif question.type == QuestionType.numerical:
            try:
                val_resp = float(resp_clean.replace(",", ""))
                val_ans = float(ans_clean.replace(",", ""))
                is_correct = abs(val_resp - val_ans) <= (0.01 * abs(val_ans) + 1e-5)
                score = 1.0 if is_correct else 0.0
                feedback = (
                    "Correct numerical computation!"
                    if is_correct
                    else f"Calculated value was incorrect. Expected: {question.answer_key}."
                )
                return {
                    "score": score,
                    "is_correct": is_correct,
                    "feedback": feedback,
                }
            except Exception:
                pass  # Fall through to rubric LLM grading

        # 3. Short Answer / Rubric LLM grading
        prompt = RUBRIC_GRADING_PROMPT.format(
            stem=question.stem,
            answer_key=question.answer_key,
            explanation=question.explanation or "",
            student_response=resp_clean,
        )

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and "score" in res:
                score = float(res["score"])
                return {
                    "score": max(0.0, min(1.0, score)),
                    "is_correct": bool(res.get("is_correct", score >= 0.7)),
                    "feedback": str(res.get("feedback", "Graded successfully.")),
                }
        except Exception as exc:
            logger.warning("LLM rubric grading fallback: %s", exc)

        # Fallback string overlap heuristic
        is_sub = ans_clean.lower() in resp_clean.lower() or resp_clean.lower() in ans_clean.lower()
        return {
            "score": 1.0 if is_sub else 0.3,
            "is_correct": is_sub,
            "feedback": "Graded using keyword presence." if is_sub else "Response was incomplete.",
        }

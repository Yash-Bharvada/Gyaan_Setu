"""Assessment Question Generator module.

Generates grounded Multiple Choice Questions (MCQ), Short Answer questions,
and Numerical problems with explicit distractor rationales and source unit links.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.llm.base import LLMClient
from app.models import QuestionType, Topic, Unit

logger = logging.getLogger(__name__)

QUESTION_GEN_PROMPT = """You are an expert assessment author and exam creator.
Generate high quality academic assessment questions strictly grounded in the following context units.

Context Material:
{context}

Target Topic: {topic_name}
Question Type: {question_type}
Difficulty (1=easy, 3=medium, 5=hard): {difficulty}

Generate 2 distinct questions. Return a valid JSON object matching this schema:
{{
  "questions": [
    {{
      "type": "{question_type}",
      "stem": "Clear, unambiguous question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],  // only for mcq
      "answer_key": "Exact correct answer string or correct option text",
      "explanation": "Detailed explanation citing the concept",
      "distractor_rationales": {{
        "Option A": "Why this option is incorrect",
        "Option C": "Why this option is incorrect",
        "Option D": "Why this option is incorrect"
      }},
      "difficulty": {difficulty}
    }}
  ]
}}
"""


class QuestionGenerator:
    @staticmethod
    def generate_questions(
        units: List[Unit],
        topic: Topic,
        llm: LLMClient,
        question_type: QuestionType = QuestionType.mcq,
        difficulty: int = 3,
    ) -> List[Dict[str, Any]]:
        """Generate assessment questions grounded in content units."""
        context_str = "\n\n".join([f"[Unit {u.id}]: {u.text[:400]}" for u in units[:5]])
        if not context_str:
            context_str = f"General concepts of {topic.name}: {topic.summary or ''}"

        prompt = QUESTION_GEN_PROMPT.format(
            context=context_str,
            topic_name=topic.name,
            question_type=question_type.value,
            difficulty=difficulty,
        )

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and "questions" in res:
                return res["questions"]
            elif isinstance(res, list):
                return res
        except Exception as exc:
            logger.warning("LLM question generator fallback: %s", exc)

        # Fallback question template
        if question_type == QuestionType.mcq:
            return [
                {
                    "type": "mcq",
                    "stem": f"Which of the following is the primary principle of {topic.name}?",
                    "options": [
                        f"Fundamental mechanism of {topic.name}",
                        "An unrelated physical phenomenon",
                        "Arbitrary static property",
                        "Inverse non-linear assumption",
                    ],
                    "answer_key": f"Fundamental mechanism of {topic.name}",
                    "explanation": f"The core foundation of {topic.name} establishes this primary mechanism.",
                    "distractor_rationales": {
                        "An unrelated physical phenomenon": "This refers to an entirely separate domain.",
                        "Arbitrary static property": "Does not explain the mechanism.",
                        "Inverse non-linear assumption": "Factually incorrect description.",
                    },
                    "difficulty": difficulty,
                }
            ]
        else:
            return [
                {
                    "type": question_type.value,
                    "stem": f"Explain the key concept and mechanism of {topic.name}.",
                    "answer_key": f"{topic.name} is characterized by {topic.summary or 'its core principle'}.",
                    "explanation": f"Grounded in unit materials for {topic.name}.",
                    "difficulty": difficulty,
                }
            ]

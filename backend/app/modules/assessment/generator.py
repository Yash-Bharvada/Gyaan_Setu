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

Generate {count} distinct, high-yield questions directly testing understanding of {topic_name}.
Return a valid JSON object matching this schema exactly with NO comments:
{{
  "questions": [
    {{
      "type": "{question_type}",
      "stem": "Clear, unambiguous academic question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer_key": "Exact correct answer string from the options list",
      "explanation": "Detailed step-by-step academic explanation citing the concept and source facts",
      "distractor_rationales": {{
        "Option A": "Why this distractor is incorrect based on the material",
        "Option C": "Why this distractor is incorrect based on the material",
        "Option D": "Why this distractor is incorrect based on the material"
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
        count: int = 2,
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
            count=count,
        )

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and "questions" in res:
                return res["questions"]
            elif isinstance(res, list):
                return res
        except Exception as exc:
            logger.warning("LLM question generator fallback: %s", exc)

        # Grounded fallback question from unit text
        summary_text = topic.summary or f"The fundamental principles and operational mechanisms of {topic.name}."
        first_unit_text = ""
        for u in units:
            if u.text and len(u.text.strip()) > 30:
                first_unit_text = u.text.strip()
                break

        if question_type == QuestionType.mcq:
            correct_ans = first_unit_text[:140] if first_unit_text else summary_text
            return [
                {
                    "type": "mcq",
                    "stem": f"In {topic.name}, which statement is directly supported by the study material?",
                    "options": [
                        correct_ans,
                        f"It assumes that all features are perfectly independent without any correlation.",
                        f"It eliminates the need for any mathematical or computational evaluation.",
                        f"It operates exclusively on static non-differentiable step constants.",
                    ],
                    "answer_key": correct_ans,
                    "explanation": f"Grounded in curriculum context for {topic.name}.",
                    "distractor_rationales": {
                        f"It assumes that all features are perfectly independent without any correlation.": "Unsupported assumption.",
                        f"It eliminates the need for any mathematical or computational evaluation.": "Contradicts curriculum methodology.",
                        f"It operates exclusively on static non-differentiable step constants.": "Factually incorrect constraint.",
                    },
                    "difficulty": difficulty,
                }
            ]
        else:
            return [
                {
                    "type": question_type.value,
                    "stem": f"Based on the curriculum for {topic.name}, explain how its core methodology functions.",
                    "answer_key": first_unit_text[:200] if first_unit_text else summary_text,
                    "explanation": f"Grounded in study guide units for {topic.name}.",
                    "difficulty": difficulty,
                }
            ]

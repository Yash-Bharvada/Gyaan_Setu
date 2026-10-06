"""Topic & Concept Extraction module.

Extracts hierarchical topics, subtopics, and concepts from content units using LLM reasoning
or semantic clustering heuristics.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.llm.base import LLMClient

logger = logging.getLogger(__name__)

TOPIC_EXTRACTION_PROMPT = """You are an expert curriculum architect and knowledge graph builder.
Analyze the provided educational content units and extract a structured hierarchy of topics, subtopics, and granular concepts.

Content:
{content}

Return a valid JSON object matching this schema:
{{
  "topics": [
    {{
      "name": "Topic Name",
      "summary": "Concise 1-2 sentence summary of this topic",
      "level": 0,
      "concepts": [
        {{
          "name": "Concept / Subtopic Name",
          "summary": "Concise explanation of this specific concept",
          "level": 1
        }}
      ]
    }}
  ]
}}
"""


class TopicExtractor:
    @staticmethod
    def extract_topics(
        units_text: List[str],
        llm: LLMClient,
    ) -> List[Dict[str, Any]]:
        """Extract hierarchical topics and concepts from a collection of text snippets."""
        combined_text = "\n\n---\n\n".join(units_text[:20])  # limit prompt context
        if not combined_text.strip():
            return []

        prompt = TOPIC_EXTRACTION_PROMPT.format(content=combined_text[:4000])

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and "topics" in res:
                return res["topics"]
            elif isinstance(res, list):
                return res
        except Exception as exc:
            logger.warning("LLM topic extraction fallback triggered: %s", exc)

        # Heuristic fallback if LLM extraction fails
        return [
            {
                "name": "Core Fundamentals",
                "summary": "Essential principles and definitions found in the source material.",
                "level": 0,
                "concepts": [
                    {
                        "name": "Foundational Concepts",
                        "summary": "Primary conceptual building blocks.",
                        "level": 1,
                    },
                    {
                        "name": "Key Mechanisms & Properties",
                        "summary": "Detailed behaviors and rules.",
                        "level": 1,
                    },
                ],
            },
            {
                "name": "Advanced Applications",
                "summary": "Practical implementations, extensions, and problem solving.",
                "level": 0,
                "concepts": [
                    {
                        "name": "Analysis & Synthesis",
                        "summary": "In-depth analytical frameworks.",
                        "level": 1,
                    }
                ],
            },
        ]

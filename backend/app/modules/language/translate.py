"""Cross-Lingual Translation & Query Expansion module.

Translates Hindi / Hinglish queries to academic English for cross-lingual vector retrieval,
and translates English explanations into student's preferred language.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.llm.base import LLMClient
from app.modules.language.detect import detect_language

logger = logging.getLogger(__name__)

TRANSLATE_PROMPT = """Translate the following text into clear, academic {target_lang}.
Preserve technical terminology and conceptual meaning accurately.

Text: "{text}"

Translation:"""


class Translator:
    @staticmethod
    def translate_text(
        text: str,
        target_lang: str,
        llm: LLMClient,
    ) -> str:
        """Translate text into target language ('en', 'hi', 'hi-Latn')."""
        if not text.strip():
            return text

        current_lang = detect_language(text)
        if current_lang == target_lang or (current_lang == "en" and target_lang == "en"):
            return text

        lang_name = "English" if target_lang == "en" else ("Hindi (Devanagari script)" if target_lang == "hi" else "Hinglish (Hindi written in Roman English letters)")
        prompt = TRANSLATE_PROMPT.format(target_lang=lang_name, text=text)

        try:
            return llm.generate(prompt=prompt, system="You are a precise multilingual academic translator.").strip()
        except Exception as exc:
            logger.warning("Translation LLM fallback: %s", exc)
            return text

    @staticmethod
    def expand_query_for_retrieval(
        query: str,
        llm: LLMClient,
    ) -> str:
        """Expand and translate non-English query into English for vector and BM25 search."""
        lang = detect_language(query)
        if lang in ["hi", "hi-Latn"]:
            english_q = Translator.translate_text(query, target_lang="en", llm=llm)
            # Combine original + translated for maximum recall
            return f"{english_q} {query}"
        return query

"""
LLM client factory.

Builds the provider chain from the ``LLM_CHAIN`` setting and returns a
singleton ``LLMClient`` ready for use.  Falls back to ``MockLLM`` when
``GROQ_API_KEY`` is absent (useful for CI / offline tests).

Usage::

    from app.llm.factory import get_llm
    llm = get_llm()
    text = llm.generate("Hello")
"""
from __future__ import annotations

import logging
import os
from typing import List

from app.core.config import settings
from app.llm.base import LLMClient

logger = logging.getLogger(__name__)

_llm: LLMClient | None = None


def _build_chain() -> LLMClient:
    providers: List[LLMClient] = []
    chain = settings.llm_chain_list

    for name in chain:
        name = name.strip().lower()
        if name == "groq":
            if not settings.GROQ_API_KEY:
                logger.warning("GROQ_API_KEY not set; skipping groq provider")
                continue
            from app.llm.groq import GroqClient
            providers.append(GroqClient())

        elif name == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not set; skipping gemini provider")
                continue
            try:
                from app.llm.gemini import GeminiClient
                providers.append(GeminiClient())
            except ImportError:
                logger.warning("google-generativeai not installed; skipping gemini")

        elif name == "ollama":
            try:
                from app.llm.ollama import OllamaClient
                providers.append(OllamaClient())
            except Exception as exc:
                logger.warning("Failed to init Ollama: %s", exc)

        else:
            logger.warning("Unknown LLM provider in chain: %s", name)

    if not providers:
        logger.warning("No real LLM providers available — using MockLLM")
        from app.llm.mock import MockLLM
        return MockLLM()

    if len(providers) == 1:
        return providers[0]

    from app.llm.fallback import FallbackChain
    return FallbackChain(providers)


def get_llm() -> LLMClient:
    """Return the singleton LLM client (thread-safe lazy init)."""
    global _llm
    if _llm is None:
        _llm = _build_chain()
    return _llm


def reset_llm(client: LLMClient | None = None) -> None:
    """Replace the singleton — useful in tests to inject MockLLM."""
    global _llm
    _llm = client

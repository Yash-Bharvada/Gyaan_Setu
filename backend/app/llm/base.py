"""Abstract LLMClient interface — every provider must implement this."""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel


class LLMClient(abc.ABC):
    """
    All LLM calls in the system go through this interface.

    Roles
    -----
    - ``generator``: uses GROQ_MODEL_GENERATOR (or equivalent)
    - ``verifier``:  uses GROQ_MODEL_VERIFIER (a *different* model family)
    """

    # ── Text generation ──────────────────────────────────────────────────────

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        bypass_cache: bool = False,
    ) -> str:
        """Generate a text completion.  Returns the assistant turn as a string."""

    @abc.abstractmethod
    def generate_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        repair_retry: int = 1,
        bypass_cache: bool = False,
    ) -> BaseModel:
        """
        Generate and parse structured JSON matching *schema*.

        On parse failure, a repair pass is attempted up to *repair_retry* times
        before raising ``LLMError``.
        """

    # ── Embeddings (always local, never metered) ─────────────────────────────

    @abc.abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for *texts* using the local sentence-transformer."""

    # ── Vision ───────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def describe_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe this image concisely and factually.",
        bypass_cache: bool = False,
    ) -> str:
        """Return a textual description of the image."""

    # ── Transcription (always local faster-whisper) ──────────────────────────

    @abc.abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Transcribe an audio file with timestamps.

        Returns a list of segments::

            [{"text": str, "start": float, "end": float}, ...]
        """

    # ── Usage counters ────────────────────────────────────────────────────────

    @abc.abstractmethod
    def get_usage(self) -> Dict[str, Any]:
        """Return usage counters for ``GET /api/v1/admin/llm-usage``."""

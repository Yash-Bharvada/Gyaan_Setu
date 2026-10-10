"""
Optional Gemini free-tier client.

Import-guarded so the app starts without google-generativeai installed
as long as LLM_CHAIN does not include 'gemini'.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import LLMError
from app.llm.base import LLMClient
from app.llm.ratelimit import RateLimiter
import app.llm.embeddings_local as _emb

logger = logging.getLogger(__name__)


class GeminiClient(LLMClient):
    """Optional Gemini free-tier provider."""

    PROVIDER = "gemini"

    def __init__(self):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is not installed; run: pip install google-generativeai"
            ) from exc
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._genai = genai
        self._limiter = RateLimiter(
            rpm=settings.GEMINI_RATE_LIMIT_RPM,
            concurrency=settings.GEMINI_CONCURRENCY,
            provider=self.PROVIDER,
        )
        self._calls: Dict[str, int] = {}

    def _model(self, role: str):
        # Gemini: use same model for both roles (no separate verifier model)
        return self._genai.GenerativeModel("gemini-1.5-flash")

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        bypass_cache: bool = False,
    ) -> str:
        self._calls[f"generate_{role}"] = self._calls.get(f"generate_{role}", 0) + 1

        def _call():
            m = self._model(role)
            resp = m.generate_content(
                (f"{system}\n\n" if system else "") + prompt,
                generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
            )
            return resp.text or ""

        try:
            return self._limiter.call(_call)
        except Exception as exc:
            raise LLMError(f"Gemini generate failed: {exc}") from exc

    def generate_json(
        self,
        prompt: str,
        schema: Type[BaseModel] | None = None,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        repair_retry: int = 1,
        bypass_cache: bool = False,
    ) -> Any:
        import json
        if schema is not None:
            schema_str = json.dumps(schema.model_json_schema(), indent=2)
            sys_msg = (system or "") + f"\nRespond ONLY with valid JSON matching:\n{schema_str}"
        else:
            sys_msg = (system or "") + "\nRespond ONLY with valid JSON."
        raw = self.generate(prompt, sys_msg, role, temperature, max_tokens, bypass_cache)
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```")
        try:
            return schema.model_validate_json(raw) if schema is not None else json.loads(raw)
        except Exception as exc:
            if repair_retry <= 0:
                raise LLMError(f"Gemini JSON parse failed: {exc}") from exc
            raw2 = self.generate(
                f"Fix this JSON:\n{raw}\nError: {exc}", sys_msg, role, temperature, max_tokens, True
            )
            raw2 = raw2.strip().lstrip("```json").lstrip("```").rstrip("```")
            try:
                return schema.model_validate_json(raw2) if schema is not None else json.loads(raw2)
            except Exception as exc2:
                raise LLMError(f"Gemini JSON repair failed: {exc2}") from exc2

    def embed(self, texts: List[str]) -> List[List[float]]:
        return _emb.embed(texts, settings.EMBEDDING_MODEL, settings.EMBEDDING_BATCH_SIZE)

    def describe_image(self, image_bytes: bytes, prompt: str = "Describe this image.", bypass_cache: bool = False) -> str:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        m = self._genai.GenerativeModel("gemini-1.5-flash")

        def _call():
            resp = m.generate_content([prompt, img])
            return resp.text or ""

        return self._limiter.call(_call)

    def transcribe(self, audio_path: str, language: str | None = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Gemini transcribe not implemented; use faster-whisper via GroqClient")

    def get_usage(self) -> Dict[str, Any]:
        return {"provider": self.PROVIDER, "calls": self._calls}

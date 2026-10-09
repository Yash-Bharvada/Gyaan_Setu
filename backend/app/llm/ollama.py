"""
Optional Ollama local client (free, no quota).

Uses the Ollama OpenAI-compatible REST endpoint.
Enabled by setting LLM_CHAIN=groq,ollama or LLM_CHAIN=ollama.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Type

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import LLMError
from app.llm.base import LLMClient
from app.llm.ratelimit import RateLimiter
import app.llm.embeddings_local as _emb

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """Local Ollama provider — zero quota."""

    PROVIDER = "ollama"

    def __init__(self):
        self._base = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        self._limiter = RateLimiter(
            rpm=999,  # effectively unlimited
            concurrency=settings.OLLAMA_CONCURRENCY,
            provider=self.PROVIDER,
        )
        self._calls: Dict[str, int] = {}

    def _chat(self, messages: list, temperature: float, max_tokens: int) -> str:
        url = f"{self._base}/api/chat"
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        def _call():
            resp = httpx.post(url, json=payload, timeout=120.0)
            resp.raise_for_status()
            return resp.json()["message"]["content"]

        return self._limiter.call(_call)

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
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            return self._chat(messages, temperature, max_tokens)
        except Exception as exc:
            raise LLMError(f"Ollama generate failed: {exc}") from exc

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
        schema_str = json.dumps(schema.model_json_schema(), indent=2)
        sys_msg = (system or "") + f"\nRespond ONLY with valid JSON:\n{schema_str}"
        raw = self.generate(prompt, sys_msg, role, temperature, max_tokens)
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```")
        try:
            return schema.model_validate_json(raw)
        except Exception as exc:
            if repair_retry <= 0:
                raise LLMError(f"Ollama JSON parse failed: {exc}") from exc
            raw2 = self.generate(f"Fix JSON:\n{raw}\nError: {exc}", sys_msg)
            try:
                return schema.model_validate_json(raw2.strip())
            except Exception as exc2:
                raise LLMError(f"Ollama JSON repair failed: {exc2}") from exc2

    def embed(self, texts: List[str]) -> List[List[float]]:
        return _emb.embed(texts, settings.EMBEDDING_MODEL, settings.EMBEDDING_BATCH_SIZE)

    def describe_image(self, image_bytes: bytes, prompt: str = "Describe this image.", bypass_cache: bool = False) -> str:
        raise NotImplementedError("Ollama vision not implemented in this version")

    def transcribe(self, audio_path: str, language: str | None = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Use faster-whisper via GroqClient")

    def get_usage(self) -> Dict[str, Any]:
        return {"provider": self.PROVIDER, "model": self._model, "calls": self._calls}

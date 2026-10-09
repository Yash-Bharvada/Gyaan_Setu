"""
Groq LLM client.

Wraps the official ``groq`` SDK (OpenAI-compatible) with:
  - Persistent response cache (via cache.py)
  - Token-bucket rate limiter + concurrency semaphore (via ratelimit.py)
  - generate_json with one-shot parse and one repair retry
  - Local sentence-transformer for embed()
  - Local faster-whisper for transcribe()
  - describe_image via the Groq vision model

All model names come from settings — never hardcoded.
"""
from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.errors import LLMError
from app.llm.base import LLMClient
from app.llm.cache import cached_call
from app.llm.ratelimit import RateLimiter
import app.llm.embeddings_local as _emb

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        size = settings.WHISPER_MODEL
        logger.info("Loading faster-whisper model: %s", size)
        _whisper_model = WhisperModel(size, device="cpu", compute_type="int8")
        logger.info("faster-whisper ready")
    return _whisper_model


class GroqClient(LLMClient):
    """Primary LLM client using the Groq free-tier API."""

    PROVIDER = "groq"

    def __init__(self):
        import groq as _groq  # noqa: PLC0415

        self._client = _groq.Groq(api_key=settings.GROQ_API_KEY)
        self._limiter = RateLimiter(
            rpm=settings.GROQ_RATE_LIMIT_RPM,
            concurrency=settings.GROQ_CONCURRENCY,
            provider=self.PROVIDER,
        )
        self._calls: Dict[str, int] = {}
        self._tokens_used: int = 0

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _model_for_role(self, role: str) -> str:
        return (
            settings.GROQ_MODEL_VERIFIER
            if role == "verifier"
            else settings.GROQ_MODEL_GENERATOR
        )

    def _chat(
        self,
        prompt: str,
        system: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        def _call():
            resp = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            usage = resp.usage
            if usage:
                self._tokens_used += usage.total_tokens or 0
            return resp.choices[0].message.content or ""

        return self._limiter.call(_call)

    def _raw_generate(
        self,
        prompt: str,
        system: str,
        model: str,
        temperature: float,
        max_tokens: int,
        bypass_cache: bool,
    ) -> str:
        result, hit = cached_call(
            cache_dir=settings.LLM_CACHE_DIR,
            provider=self.PROVIDER,
            model=model,
            system=system or "",
            prompt=prompt,
            params={"temperature": temperature, "max_tokens": max_tokens},
            bypass=bypass_cache,
            fn=lambda: self._chat(prompt, system or "", model, temperature, max_tokens),
        )
        key = "cache_hit" if hit else "cache_miss"
        self._calls[key] = self._calls.get(key, 0) + 1
        return result

    # ── Public interface ─────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        bypass_cache: bool = False,
    ) -> str:
        model = self._model_for_role(role)
        key = f"generate_{role}"
        self._calls[key] = self._calls.get(key, 0) + 1
        try:
            return self._raw_generate(prompt, system, model, temperature, max_tokens, bypass_cache)
        except Exception as exc:
            raise LLMError(f"Groq generate failed: {exc}") from exc

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
        model = self._model_for_role(role)
        key = f"generate_json_{role}"
        self._calls[key] = self._calls.get(key, 0) + 1

        if schema is not None:
            schema_str = json.dumps(schema.model_json_schema(), indent=2)
            sys_msg = (system or "") + (
                f"\n\nRespond ONLY with valid JSON matching this schema:\n{schema_str}"
            )
        else:
            sys_msg = (system or "") + "\n\nRespond ONLY with valid JSON. Do not include markdown or explanations outside the JSON."

        raw = self._raw_generate(prompt, sys_msg, model, temperature, max_tokens, bypass_cache)

        def _parse(text: str) -> Any:
            # Strip markdown fences if present
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            if schema is not None:
                return schema.model_validate_json(text)
            return json.loads(text)

        try:
            return _parse(raw)
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            if repair_retry <= 0:
                raise LLMError(f"JSON parse failed, no retries left: {exc}") from exc
            # Repair: send the bad output back with the error
            repair_prompt = (
                f"The previous response was not valid JSON:\n\n{raw}\n\n"
                f"Error: {exc}\n\nPlease output ONLY valid JSON matching the schema."
            )
            logger.warning("generate_json: parse failed, attempting repair")
            raw2 = self._raw_generate(
                repair_prompt, sys_msg, model, temperature, max_tokens, bypass_cache=True
            )
            try:
                return _parse(raw2)
            except (ValidationError, ValueError, json.JSONDecodeError) as exc2:
                raise LLMError(f"JSON parse failed after repair: {exc2}") from exc2

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Always uses the local sentence-transformer — never Groq quota."""
        return _emb.embed(
            texts,
            model_name=settings.EMBEDDING_MODEL,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
        )

    def describe_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe this image concisely and factually.",
        bypass_cache: bool = False,
    ) -> str:
        import base64
        b64 = base64.b64encode(image_bytes).decode()
        full_prompt = f"data:image/png;base64,{b64}"  # noqa: unused
        # Groq vision model uses messages with image_url content parts
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}",
                        },
                    },
                ],
            }
        ]

        def _call():
            resp = self._client.chat.completions.create(
                model=settings.GROQ_VISION_MODEL,
                messages=messages,
                max_tokens=512,
            )
            return resp.choices[0].message.content or ""

        self._calls["describe_image"] = self._calls.get("describe_image", 0) + 1
        key = "describe_image"
        # Use cache keyed on content hash
        import hashlib
        img_hash = hashlib.md5(image_bytes).hexdigest()
        result, _ = cached_call(
            cache_dir=settings.LLM_CACHE_DIR,
            provider=self.PROVIDER,
            model=settings.GROQ_VISION_MODEL,
            system="",
            prompt=f"{prompt}::{img_hash}",
            params={},
            bypass=bypass_cache,
            fn=lambda: self._limiter.call(_call),
        )
        return result

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> List[Dict[str, Any]]:
        model = _get_whisper()
        segments_gen, _info = model.transcribe(
            audio_path,
            language=language,
            vad_filter=True,
            beam_size=5,
        )
        self._calls["transcribe"] = self._calls.get("transcribe", 0) + 1
        return [
            {"text": seg.text.strip(), "start": seg.start, "end": seg.end}
            for seg in segments_gen
        ]

    def get_usage(self) -> Dict[str, Any]:
        return {
            "provider": self.PROVIDER,
            "model_generator": settings.GROQ_MODEL_GENERATOR,
            "model_verifier": settings.GROQ_MODEL_VERIFIER,
            "calls": self._calls,
            "tokens_used": self._tokens_used,
        }

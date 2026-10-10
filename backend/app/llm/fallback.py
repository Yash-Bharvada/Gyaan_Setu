"""
Fallback chain LLM client.

Wraps a list of ``LLMClient`` instances and tries each in order when the
previous one raises an exception (typically 429 / 5xx / timeout).

Exponential back-off with jitter is applied between retries of the *same*
provider before moving on to the next.
"""
from __future__ import annotations

import logging
import random
import time
from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel

from app.core.errors import LLMError
from app.llm.base import LLMClient

logger = logging.getLogger(__name__)

_RETRYABLE_CODES = {429, 500, 502, 503, 504}


def _should_retry(exc: Exception) -> bool:
    """Return True for 429 / 5xx errors."""
    msg = str(exc).lower()
    return any(str(c) in msg for c in _RETRYABLE_CODES) or "rate" in msg or "timeout" in msg


def _backoff(attempt: int) -> float:
    base = min(60.0, 2 ** attempt)
    return base + random.uniform(0, base * 0.2)


class FallbackChain(LLMClient):
    """
    Tries each provider in *providers* order.

    On 429/5xx, applies exponential back-off for up to *per_provider_retries*
    before moving to the next provider.
    """

    def __init__(self, providers: List[LLMClient], per_provider_retries: int = 2):
        self._providers = providers
        self._retries = per_provider_retries
        self._calls: Dict[str, int] = {}

    def _call_with_fallback(self, method: str, *args, **kwargs):
        last_exc: Exception | None = None
        for provider in self._providers:
            fn = getattr(provider, method)
            for attempt in range(self._retries + 1):
                try:
                    result = fn(*args, **kwargs)
                    self._calls[f"{provider.PROVIDER}.{method}"] = (
                        self._calls.get(f"{provider.PROVIDER}.{method}", 0) + 1
                    )
                    return result
                except Exception as exc:
                    last_exc = exc
                    if _should_retry(exc) and attempt < self._retries:
                        wait = _backoff(attempt)
                        logger.warning(
                            "Provider %s/%s attempt %d failed (%s); retrying in %.1fs",
                            provider.PROVIDER, method, attempt + 1, exc, wait,
                        )
                        time.sleep(wait)
                    else:
                        logger.warning(
                            "Provider %s/%s failed; trying next: %s",
                            provider.PROVIDER, method, exc,
                        )
                        break
        raise LLMError(f"All providers failed for {method}: {last_exc}")

    @property
    def PROVIDER(self) -> str:  # type: ignore[override]
        return "fallback_chain"

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        bypass_cache: bool = False,
    ) -> str:
        return self._call_with_fallback(
            "generate", prompt, system=system, role=role,
            temperature=temperature, max_tokens=max_tokens, bypass_cache=bypass_cache,
        )

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
        return self._call_with_fallback(
            "generate_json", prompt, schema, system=system, role=role,
            temperature=temperature, max_tokens=max_tokens,
            repair_retry=repair_retry, bypass_cache=bypass_cache,
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        # Always use the first provider's embed (always local)
        return self._providers[0].embed(texts)

    def describe_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe this image concisely and factually.",
        bypass_cache: bool = False,
    ) -> str:
        return self._call_with_fallback("describe_image", image_bytes, prompt=prompt, bypass_cache=bypass_cache)

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> List[Dict[str, Any]]:
        # Always use the first provider that supports transcribe (GroqClient → local whisper)
        return self._providers[0].transcribe(audio_path, language=language)

    def get_usage(self) -> Dict[str, Any]:
        all_usage = {}
        for p in self._providers:
            all_usage[p.PROVIDER] = p.get_usage()
        all_usage["chain_calls"] = self._calls
        return all_usage

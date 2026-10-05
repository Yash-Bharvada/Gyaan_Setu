"""
Deterministic MockLLM for offline tests — never touches any external API.

Behaviour
---------
- ``generate()``         → echoes back a labelled stub string
- ``generate_json()``    → returns a schema-specific canned Pydantic object
- ``embed()``            → hash-based deterministic float vectors (length = dim)
- ``describe_image()``   → canned description string
- ``transcribe()``       → synthetic timestamped segments from a counter
- ``get_usage()``        → always-zero counters
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel

from app.llm.base import LLMClient


_DEFAULT_DIM = 384


def _hash_embed(text: str, dim: int = _DEFAULT_DIM) -> List[float]:
    """Deterministic pseudo-embedding based on SHA-256 of text."""
    digest = hashlib.sha256(text.encode()).digest()  # 32 bytes
    # Repeat until we have enough values, then normalise
    repeated = (digest * (dim // 32 + 1))[:dim]
    raw = [b / 255.0 - 0.5 for b in repeated]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [x / norm for x in raw]


class MockLLM(LLMClient):
    """100 % offline mock — safe to use from any test."""

    PROVIDER: str = "mock"

    def __init__(self, dim: int = _DEFAULT_DIM):
        self._dim = dim
        self._calls: Dict[str, int] = {}

    def _count(self, key: str):
        self._calls[key] = self._calls.get(key, 0) + 1

    # ── Text generation ──────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        bypass_cache: bool = False,
    ) -> str:
        self._count(f"generate_{role}")
        return f"[MOCK-{role.upper()}] response to: {prompt[:60]}"

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
        self._count(f"generate_json_{role}")
        # Build a minimal valid instance by filling required fields with sensible stubs
        fields = schema.model_fields
        data: Dict[str, Any] = {}
        for name, field_info in fields.items():
            ann = field_info.annotation
            # Strip Optional / Union
            origin = getattr(ann, "__origin__", None)
            args = getattr(ann, "__args__", ())
            # Unwrap Optional[X]
            if origin is type(None):
                data[name] = None
                continue
            if origin is not None and type(None) in args:
                # Optional → pick the non-None type
                inner = next((a for a in args if a is not type(None)), str)
                ann = inner

            if ann is str:
                data[name] = f"mock_{name}"
            elif ann is int:
                data[name] = 1
            elif ann is float:
                data[name] = 1.0
            elif ann is bool:
                data[name] = True
            elif ann is list or (origin is list):
                data[name] = []
            elif ann is dict or (origin is dict):
                data[name] = {}
            else:
                data[name] = None
        return schema.model_validate(data)

    # ── Embeddings ───────────────────────────────────────────────────────────

    def embed(self, texts: List[str]) -> List[List[float]]:
        self._count("embed")
        return [_hash_embed(t, self._dim) for t in texts]

    # ── Vision ───────────────────────────────────────────────────────────────

    def describe_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe this image concisely and factually.",
        bypass_cache: bool = False,
    ) -> str:
        self._count("describe_image")
        digest = hashlib.md5(image_bytes).hexdigest()[:8]
        return f"[MOCK] Image description for hash={digest}"

    # ── Transcription ────────────────────────────────────────────────────────

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> List[Dict[str, Any]]:
        self._count("transcribe")
        # Return two synthetic 30-second segments
        return [
            {"text": "Mock transcript segment one.", "start": 0.0, "end": 30.0},
            {"text": "Mock transcript segment two.", "start": 30.0, "end": 60.0},
        ]

    # ── Usage ────────────────────────────────────────────────────────────────

    def get_usage(self) -> Dict[str, Any]:
        return {"provider": "mock", "calls": self._calls, "cost": 0.0}

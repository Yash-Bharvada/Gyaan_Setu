"""Local sentence-transformer embedder — CPU, no quota, lazy-loaded singleton."""
from __future__ import annotations

import hashlib
import logging
import math
from typing import List

logger = logging.getLogger(__name__)

_model = None
_dim: int = 384
_model_name: str = ""
_use_fallback: bool = False


def _hash_embed(text: str, dim: int = 384) -> List[float]:
    """Deterministic pseudo-embedding based on SHA-256 of text."""
    digest = hashlib.sha256(text.encode()).digest()
    repeated = (digest * (dim // 32 + 1))[:dim]
    raw = [b / 255.0 - 0.5 for b in repeated]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [x / norm for x in raw]


def _load(model_name: str):
    global _model, _dim, _model_name, _use_fallback
    if _model is not None and _model_name == model_name:
        return
    if _use_fallback:
        return

    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading local embedder: %s", model_name)
        _model = SentenceTransformer(model_name)
        _dim = _model.get_sentence_embedding_dimension()
        _model_name = model_name
        logger.info("Embedder ready — dim=%d", _dim)
    except Exception as exc:
        logger.warning(
            "SentenceTransformer failed to load (%s). Falling back to deterministic pseudo-embeddings.",
            exc,
        )
        _use_fallback = True
        _dim = 384
        _model_name = "fallback-hash-embed"


def get_dim(model_name: str) -> int:
    _load(model_name)
    return _dim


def get_model_name() -> str:
    return _model_name


def embed(texts: List[str], model_name: str, batch_size: int = 32) -> List[List[float]]:
    """Embed a list of texts; returns list of float lists."""
    if not texts:
        return []

    _load(model_name)

    if _use_fallback or _model is None:
        return [_hash_embed(t, _dim) for t in texts]

    try:
        vecs = _model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vecs.tolist()
    except Exception as exc:
        logger.warning("Local embedding encode failed (%s). Using fallback embeddings.", exc)
        return [_hash_embed(t, _dim) for t in texts]


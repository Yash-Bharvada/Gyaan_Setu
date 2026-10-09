"""Local sentence-transformer embedder — CPU, no quota, lazy-loaded singleton."""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)

_model = None
_dim: int = 0
_model_name: str = ""


def _load(model_name: str):
    global _model, _dim, _model_name
    if _model is not None and _model_name == model_name:
        return
    from sentence_transformers import SentenceTransformer

    logger.info("Loading local embedder: %s", model_name)
    _model = SentenceTransformer(model_name)
    _dim = _model.get_sentence_embedding_dimension()
    _model_name = model_name
    logger.info("Embedder ready — dim=%d", _dim)


def get_dim(model_name: str) -> int:
    _load(model_name)
    return _dim


def get_model_name() -> str:
    return _model_name


def embed(texts: List[str], model_name: str, batch_size: int = 32) -> List[List[float]]:
    """Embed a list of texts; returns list of float lists."""
    _load(model_name)
    if not texts:
        return []
    vecs = _model.encode(  # type: ignore[union-attr]
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return vecs.tolist()

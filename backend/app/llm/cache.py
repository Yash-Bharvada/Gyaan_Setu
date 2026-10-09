"""
Persistent LLM response cache backed by diskcache (SQLite under the hood).

Key: sha256(provider + model + system + prompt + serialised params)
Value: the raw response string.

A ``bypass_cache=True`` flag skips the read (but still writes the fresh result).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_cache = None


def _get_cache(cache_dir: str):
    global _cache
    if _cache is None:
        import diskcache

        os.makedirs(cache_dir, exist_ok=True)
        _cache = diskcache.Cache(cache_dir)
        logger.info("LLM cache opened at %s", cache_dir)
    return _cache


def _make_key(provider: str, model: str, system: str, prompt: str, params: dict) -> str:
    payload = json.dumps(
        {"provider": provider, "model": model, "system": system, "prompt": prompt, "params": params},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def cached_call(
    cache_dir: str,
    provider: str,
    model: str,
    system: str,
    prompt: str,
    params: dict,
    bypass: bool,
    fn: Callable[[], str],
) -> tuple[str, bool]:
    """
    Return ``(result, cache_hit)``.

    ``fn`` is called only on a miss or when *bypass* is True.
    """
    cache = _get_cache(cache_dir)
    key = _make_key(provider, model, system or "", prompt, params)

    if not bypass:
        hit = cache.get(key)
        if hit is not None:
            logger.debug("Cache HIT  key=%s", key[:12])
            return hit, True

    result = fn()
    cache.set(key, result)
    logger.debug("Cache MISS key=%s", key[:12])
    return result, False

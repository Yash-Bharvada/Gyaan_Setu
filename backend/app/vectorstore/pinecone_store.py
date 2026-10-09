"""
Pinecone Starter (serverless) vector store.

Key design decisions (from Pinecone v10 docs):
- ``Pinecone(api_key=...)`` — no environment/host needed for Starter.
- ``ServerlessSpec(cloud=..., region=...)`` — Starter is limited to one region.
- ``create_index`` called once; reuses the existing index if it already exists.
- Dimension and metric are taken from the local embedder (never hardcoded).
- Upsert in batches of ≤100 vectors.
- Metadata kept SMALL: unit_id, source_id, type, topic_ids only.
  Full text lives in SQLite.
- Delete by explicit id lists tracked in the ``vector_refs`` table.
- Caches identical queries to avoid burning read-unit quota.
- Polls after upsert for eventual consistency before returning.
- On startup ping: if the index is paused, logs a clear remedy.
"""
from __future__ import annotations

import functools
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.errors import VectorStoreError
from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100
_POLL_TIMEOUT = 30.0   # seconds to wait for eventual consistency
_POLL_INTERVAL = 1.0


class PineconeStore(VectorStore):

    def __init__(self, dim: int | None = None, metric: str = "cosine"):
        from pinecone import Pinecone, ServerlessSpec

        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._dim = dim
        self._metric = metric
        self._index_name = settings.PINECONE_INDEX
        self._index = None  # lazy

        # Simple in-process query cache keyed by (ns, query_hash) → results
        self._query_cache: Dict[str, list] = {}

    # ── Index management ─────────────────────────────────────────────────────

    def _ensure_index(self):
        if self._index is not None:
            return
        from pinecone import ServerlessSpec

        existing = [i.name for i in self._pc.list_indexes()]
        if self._index_name not in existing:
            if self._dim is None:
                raise VectorStoreError(
                    "Cannot create Pinecone index: dimension not set. "
                    "Ensure the local embedder is loaded before PineconeStore is first used."
                )
            logger.info(
                "Creating Pinecone index '%s' dim=%d metric=%s cloud=%s region=%s",
                self._index_name, self._dim, self._metric,
                settings.PINECONE_CLOUD, settings.PINECONE_REGION,
            )
            self._pc.create_index(
                name=self._index_name,
                dimension=self._dim,
                metric=self._metric,
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD,
                    region=settings.PINECONE_REGION,
                ),
            )
        self._index = self._pc.Index(self._index_name)
        logger.info("Pinecone index '%s' ready", self._index_name)

    # ── VectorStore interface ────────────────────────────────────────────────

    def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        namespace: str = "units",
    ) -> None:
        self._ensure_index()
        records = [
            {"id": i, "values": v, "metadata": m}
            for i, v, m in zip(ids, vectors, metadata)
        ]
        # Batch upsert
        for start in range(0, len(records), _BATCH_SIZE):
            batch = records[start : start + _BATCH_SIZE]
            self._index.upsert(vectors=batch, namespace=namespace)
        # Poll for eventual consistency
        self._poll_until_visible(ids[-1], namespace)
        # Invalidate query cache for this namespace
        self._query_cache = {k: v for k, v in self._query_cache.items()
                             if not k.startswith(namespace + ":")}

    def _poll_until_visible(self, last_id: str, namespace: str):
        """Wait until the last upserted vector is fetchable."""
        deadline = time.monotonic() + _POLL_TIMEOUT
        while time.monotonic() < deadline:
            try:
                resp = self._index.fetch(ids=[last_id], namespace=namespace)
                if last_id in (resp.vectors or {}):
                    return
            except Exception:
                pass
            time.sleep(_POLL_INTERVAL)
        logger.warning("Pinecone eventual-consistency poll timed out for id=%s", last_id)

    def query(
        self,
        vector: List[float],
        top_k: int = 8,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "units",
    ) -> List[Dict[str, Any]]:
        self._ensure_index()
        # Cache key
        key = namespace + ":" + hashlib.sha256(
            json.dumps({"v": vector, "k": top_k, "f": filter}, sort_keys=True).encode()
        ).hexdigest()
        if key in self._query_cache:
            return self._query_cache[key]

        kwargs: Dict[str, Any] = {
            "vector": vector,
            "top_k": top_k,
            "include_metadata": True,
            "namespace": namespace,
        }
        if filter:
            kwargs["filter"] = filter

        resp = self._index.query(**kwargs)
        results = [
            {"id": m.id, "score": m.score, "metadata": m.metadata or {}}
            for m in (resp.matches or [])
        ]
        self._query_cache[key] = results
        return results

    def delete(self, ids: List[str], namespace: str = "units") -> None:
        self._ensure_index()
        self._index.delete(ids=ids, namespace=namespace)
        # Invalidate cache
        self._query_cache = {k: v for k, v in self._query_cache.items()
                             if not k.startswith(namespace + ":")}

    def count(self, namespace: str = "units") -> int:
        self._ensure_index()
        try:
            stats = self._index.describe_index_stats()
            ns_stats = (stats.namespaces or {}).get(namespace)
            return ns_stats.vector_count if ns_stats else 0
        except Exception as exc:
            logger.warning("Pinecone count failed: %s", exc)
            return -1

    def ping(self) -> Dict[str, Any]:
        try:
            self._ensure_index()
            stats = self._index.describe_index_stats()
            return {"status": "ok", "index": self._index_name, "stats": str(stats)}
        except Exception as exc:
            msg = str(exc)
            remedy = ""
            if "paused" in msg.lower() or "inactive" in msg.lower():
                remedy = (
                    " The Starter index may be paused due to inactivity. "
                    "Visit https://app.pinecone.io and click 'Resume'."
                )
            return {"status": "error", "detail": msg + remedy}

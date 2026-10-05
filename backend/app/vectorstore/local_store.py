"""
Local ChromaDB vector store — used for tests and as the offline/fallback backend.

Never used in production when VECTOR_BACKEND=pinecone.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)

_COLLECTION_PREFIX = "sc_"


class LocalStore(VectorStore):
    """Chroma-backed local vector store (CPU, no quota)."""

    def __init__(self, persist_dir: str | None = None):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        path = persist_dir or os.path.join(settings.DATA_DIR, "local_vectors")
        os.makedirs(path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=path)
        self._collections: Dict[str, Any] = {}
        logger.info("LocalStore (Chroma) at %s", path)

    def _col(self, namespace: str):
        if namespace not in self._collections:
            self._collections[namespace] = self._client.get_or_create_collection(
                name=_COLLECTION_PREFIX + namespace,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[namespace]

    def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        namespace: str = "units",
    ) -> None:
        col = self._col(namespace)
        # Chroma requires string metadata values
        safe_meta = [
            {k: str(v) if not isinstance(v, (str, int, float, bool)) else v for k, v in m.items()}
            for m in metadata
        ]
        col.upsert(ids=ids, embeddings=vectors, metadatas=safe_meta)

    def query(
        self,
        vector: List[float],
        top_k: int = 8,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "units",
    ) -> List[Dict[str, Any]]:
        col = self._col(namespace)
        kwargs: Dict[str, Any] = {
            "query_embeddings": [vector],
            "n_results": min(top_k, max(1, col.count())),
            "include": ["metadatas", "distances"],
        }
        if filter:
            kwargs["where"] = filter

        if col.count() == 0:
            return []

        result = col.query(**kwargs)
        ids_ = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        return [
            {"id": i, "score": 1.0 - d, "metadata": m}
            for i, d, m in zip(ids_, distances, metas)
        ]

    def delete(self, ids: List[str], namespace: str = "units") -> None:
        col = self._col(namespace)
        col.delete(ids=ids)

    def count(self, namespace: str = "units") -> int:
        return self._col(namespace).count()

    def ping(self) -> Dict[str, Any]:
        try:
            # Heartbeat — list collections
            self._client.list_collections()
            return {"status": "ok", "backend": "local_chroma"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

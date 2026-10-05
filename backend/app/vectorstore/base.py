"""Abstract VectorStore interface."""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional


class VectorStore(abc.ABC):

    @abc.abstractmethod
    def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        namespace: str = "units",
    ) -> None:
        """Upsert vectors (metadata must be small — no full text)."""

    @abc.abstractmethod
    def query(
        self,
        vector: List[float],
        top_k: int = 8,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "units",
    ) -> List[Dict[str, Any]]:
        """
        Return top-k matches as::

            [{"id": str, "score": float, "metadata": dict}, ...]
        """

    @abc.abstractmethod
    def delete(self, ids: List[str], namespace: str = "units") -> None:
        """Delete vectors by explicit id list (tracked in SQLite vector_refs)."""

    @abc.abstractmethod
    def count(self, namespace: str = "units") -> int:
        """Return the number of vectors in the namespace."""

    @abc.abstractmethod
    def ping(self) -> Dict[str, Any]:
        """Health check. Return {status: ok|error, detail: str}."""

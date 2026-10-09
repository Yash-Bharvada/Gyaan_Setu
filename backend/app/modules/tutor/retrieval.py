"""Hybrid Retrieval module (BM25 + Dense Vector Store).

Combines lexical search (rank-bm25) and semantic vector search using
Reciprocal Rank Fusion (RRF) to retrieve the most relevant source units.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.llm.base import LLMClient
from app.models import Unit
from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """Combine multiple ranked lists of retrieved items using RRF."""
    scores: Dict[int, float] = {}
    item_map: Dict[int, Dict[str, Any]] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            item_id = item["unit_id"]
            item_map[item_id] = item
            # RRF formula: 1 / (k + rank + 1)
            scores[item_id] = scores.get(item_id, 0.0) + (1.0 / (k + rank + 1))

    sorted_ids = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)

    results: List[Dict[str, Any]] = []
    for uid in sorted_ids[:top_n]:
        res_item = dict(item_map[uid])
        res_item["rrf_score"] = round(scores[uid], 5)
        results.append(res_item)

    return results


class HybridRetriever:
    @staticmethod
    def retrieve(
        query: str,
        db: Session,
        llm: LLMClient,
        vector_store: VectorStore,
        top_k: int = 5,
        scope_topic_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid retrieval using BM25 and dense vector search."""
        all_units = db.query(Unit).all()
        if not all_units:
            return []

        # 1. Vector Search (Dense)
        dense_results: List[Dict[str, Any]] = []
        try:
            q_emb = llm.embed(query)
            v_matches = vector_store.query(q_emb, top_k=top_k * 2, namespace="units")
            for match in v_matches:
                unit_id = match.get("metadata", {}).get("unit_id")
                if unit_id is None:
                    try:
                        unit_id = int(match["id"].replace("unit_", ""))
                    except Exception:
                        continue
                u = db.get(Unit, unit_id)
                if u:
                    dense_results.append({
                        "unit_id": u.id,
                        "text": u.text,
                        "source_id": u.source_id,
                        "source_title": u.source.title if u.source else "Source",
                        "page": u.page,
                        "slide_no": u.slide_no,
                        "ts_start": u.ts_start,
                        "ts_end": u.ts_end,
                        "type": u.type.value,
                        "score": match.get("score", 0.5),
                    })
        except Exception as exc:
            logger.warning("Vector retrieval error: %s", exc)

        # 2. BM25 Search (Sparse Lexical)
        bm25_results: List[Dict[str, Any]] = []
        try:
            tokenized_corpus = [u.text.lower().split() for u in all_units]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.lower().split()
            bm25_scores = bm25.get_scores(tokenized_query)

            # Top scoring units from BM25
            top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k * 2]
            for idx in top_bm25_indices:
                if bm25_scores[idx] > 0.0:
                    u = all_units[idx]
                    bm25_results.append({
                        "unit_id": u.id,
                        "text": u.text,
                        "source_id": u.source_id,
                        "source_title": u.source.title if u.source else "Source",
                        "page": u.page,
                        "slide_no": u.slide_no,
                        "ts_start": u.ts_start,
                        "ts_end": u.ts_end,
                        "type": u.type.value,
                        "score": float(bm25_scores[idx]),
                    })
        except Exception as exc:
            logger.warning("BM25 retrieval error: %s", exc)

        # 3. Reciprocal Rank Fusion
        if dense_results and bm25_results:
            return reciprocal_rank_fusion([dense_results, bm25_results], top_n=top_k)
        elif dense_results:
            return dense_results[:top_k]
        elif bm25_results:
            return bm25_results[:top_k]
        else:
            # Fallback direct unit slice
            fallback_units = all_units[:top_k]
            return [
                {
                    "unit_id": u.id,
                    "text": u.text,
                    "source_id": u.source_id,
                    "source_title": u.source.title if u.source else "Source",
                    "page": u.page,
                    "slide_no": u.slide_no,
                    "ts_start": u.ts_start,
                    "ts_end": u.ts_end,
                    "type": u.type.value,
                    "score": 0.5,
                }
                for u in fallback_units
            ]

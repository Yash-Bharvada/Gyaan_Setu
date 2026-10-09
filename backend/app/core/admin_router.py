"""
Health check, LLM-usage, and quota-usage admin endpoints.

GET /api/v1/health
GET /api/v1/admin/llm-usage
GET /api/v1/admin/usage
GET /api/v1/jobs/{id}
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import text

from app.core.deps import DBSession
from app.core.config import settings
from app.modules.ingestion.jobs import JobService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["Health"])
def health(db: DBSession) -> Dict[str, Any]:
    """Check DB, LLM chain, vector backend and active OCR provider."""
    result: Dict[str, Any] = {"status": "ok"}

    # DB check
    try:
        db.execute(text("SELECT 1"))
        result["db"] = "ok"
    except Exception as exc:
        result["db"] = f"error: {exc}"
        result["status"] = "degraded"

    # LLM chain check
    try:
        from app.llm.factory import get_llm
        llm = get_llm()
        result["llm"] = {"chain": settings.LLM_CHAIN, "provider": getattr(llm, "PROVIDER", "unknown")}
    except Exception as exc:
        result["llm"] = f"error: {exc}"
        result["status"] = "degraded"

    # Vector backend check
    try:
        if settings.VECTOR_BACKEND == "pinecone":
            from app.vectorstore.pinecone_store import PineconeStore
            import app.llm.embeddings_local as _emb
            dim = _emb.get_dim(settings.EMBEDDING_MODEL) if _emb._model else None
            store = PineconeStore(dim=dim)
        else:
            from app.vectorstore.local_store import LocalStore
            store = LocalStore()
        ping = store.ping()
        result["vector_backend"] = ping
        if ping.get("status") != "ok":
            result["status"] = "degraded"
    except Exception as exc:
        result["vector_backend"] = f"error: {exc}"
        result["status"] = "degraded"

    # OCR provider
    try:
        from app.ocr.mock import get_ocr_factory
        ocr = get_ocr_factory()
        result["ocr_provider"] = ocr.provider_name
    except Exception as exc:
        result["ocr_provider"] = f"error: {exc}"

    return result


@router.get("/admin/llm-usage", tags=["Admin"])
def llm_usage() -> Dict[str, Any]:
    """Usage counters per provider/model/module."""
    from app.llm.factory import get_llm
    llm = get_llm()
    return llm.get_usage()


@router.get("/admin/usage", tags=["Admin"])
def quota_usage() -> Dict[str, Any]:
    """Persisted ledger totals for freeocr.ai and Sarvam."""
    from app.quota.ledger import UsageLedger
    ledger = UsageLedger.instance()
    return {"ledger": ledger.totals_by_provider()}


@router.get("/jobs/{job_id}", tags=["Jobs"])
def get_job(job_id: int, db: DBSession) -> Dict[str, Any]:
    job = JobService.get(db, job_id)
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }

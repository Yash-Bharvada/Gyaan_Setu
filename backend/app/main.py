"""
StudyCompanion FastAPI application entry point.

Startup: init_db, load embedder, warm LLM chain.
CORS: http://localhost:3000 allowed.
API prefix: /api/v1
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.errors import register_error_handlers
from app.core.logging import add_logging_middleware, setup_logging

# ── Setup logging before everything else ─────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StudyCompanion starting up…")

    # Ensure data directories exist
    for sub in ["uploads", "local_vectors", "audio", "eval", "llm_cache"]:
        os.makedirs(os.path.join(settings.DATA_DIR, sub), exist_ok=True)

    # Create all DB tables
    init_db()
    logger.info("Database initialised")

    # Embedder and LLM chain load lazily on first use (Free-Stack Rule 5)

    # Warm the LLM chain (just builds the client; no network call)
    try:
        from app.llm.factory import get_llm
        llm = get_llm()
        logger.info("LLM chain ready: %s", getattr(llm, "PROVIDER", "custom"))
    except Exception as exc:
        logger.warning("LLM chain init failed: %s", exc)

    logger.info("Startup complete [OK]")
    yield


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="StudyCompanion API",
        description="Personalized Tutoring & Adaptive Learning backend",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_origin_regex=r".*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request ID logging ────────────────────────────────────────────────────
    add_logging_middleware(app)

    # ── Error handlers ────────────────────────────────────────────────────────
    register_error_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    from app.core.admin_router import router as admin_router
    from app.modules.ingestion.router import router as ingest_router
    from app.modules.knowledge.router import router as knowledge_router
    from app.modules.tutor.router import router as tutor_router
    from app.modules.learner.router import router as learner_router
    from app.modules.assessment.router import router as assessment_router
    from app.modules.evaluation.router import router as eval_router
    from app.modules.revision.router import router as revision_router
    from app.modules.scheduler.router import router as scheduler_router
    from app.modules.language.router import router as language_router
    from app.modules.audio.router import router as audio_router

    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(ingest_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(tutor_router, prefix="/api/v1")
    app.include_router(learner_router, prefix="/api/v1")
    app.include_router(assessment_router, prefix="/api/v1")
    app.include_router(eval_router, prefix="/api/v1")
    app.include_router(revision_router, prefix="/api/v1")
    app.include_router(scheduler_router, prefix="/api/v1")
    app.include_router(language_router, prefix="/api/v1")
    app.include_router(audio_router, prefix="/api/v1")

    return app


app = create_app()

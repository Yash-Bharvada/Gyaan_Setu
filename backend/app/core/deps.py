"""Shared FastAPI dependencies."""
from __future__ import annotations

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.llm.base import LLMClient
from app.llm.factory import get_llm
from app.ocr.base import OCRProvider
from app.ocr.mock import get_ocr_factory
from app.vectorstore.base import VectorStore
from app.vectorstore.local_store import LocalStore

DBSession = Annotated[Session, Depends(get_db)]


def get_vector_store() -> VectorStore:
    """Dependency provider for the configured VectorStore."""
    if settings.VECTOR_BACKEND == "pinecone" and settings.PINECONE_API_KEY:
        try:
            from app.vectorstore.pinecone_store import PineconeStore
            return PineconeStore()
        except Exception:
            pass
    return LocalStore()


def get_ocr_provider() -> OCRProvider:
    """Dependency provider for the configured OCR engine."""
    return get_ocr_factory()


__all__ = [
    "get_db",
    "get_llm",
    "get_vector_store",
    "get_ocr_provider",
    "DBSession",
]

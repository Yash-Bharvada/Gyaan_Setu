"""Ingestion Service.

Orchestrates document parsing, hashing, deduplication, chunking, embedding generation,
and vector database upsertion for all multimodal content types (PDF, PPTX, Video, Images, Text).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import struct
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError, DuplicateResourceError, NotFoundError
from app.llm.base import LLMClient
from app.models import EmbeddingCache, Job, Source, SourceKind, Unit, UnitType, VectorRef
from app.modules.ingestion.parsers.image import parse_image
from app.modules.ingestion.parsers.pdf import parse_pdf
from app.modules.ingestion.parsers.pptx import parse_pptx
from app.modules.ingestion.parsers.video import parse_video_audio
from app.modules.ingestion.parsers.youtube import parse_youtube_video
from app.vectorstore.base import VectorStore


logger = logging.getLogger(__name__)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def detect_source_kind(filename: str) -> SourceKind:
    """Detect source kind from filename extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return SourceKind.pdf
    elif ext in [".pptx", ".ppt"]:
        return SourceKind.pptx
    elif ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
        return SourceKind.video
    elif ext in [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]:
        return SourceKind.audio
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]:
        return SourceKind.image
    else:
        return SourceKind.pdf


class IngestionService:
    @staticmethod
    def process_file(
        db: Session,
        file_path: str,
        title: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        vector_store: Optional[VectorStore] = None,
        ocr_provider: Optional[Any] = None,
        job_id: Optional[int] = None,
    ) -> Source:
        """Process and ingest a local file, creating source, units, and vector embeddings."""
        if not os.path.exists(file_path):
            raise NotFoundError(f"File not found: {file_path}")

        file_hash = compute_file_hash(file_path)
        existing = db.query(Source).filter(Source.file_hash == file_hash).first()
        if existing:
            logger.info("File already ingested: %s (id=%d)", file_path, existing.id)
            return existing

        file_size = os.path.getsize(file_path)
        base_name = os.path.basename(file_path)
        ext = os.path.splitext(base_name)[1].lower()
        kind = detect_source_kind(base_name)
        source_title = title or os.path.splitext(base_name)[0].replace("_", " ")

        source = Source(
            title=source_title,
            kind=kind,
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            status="processing",
            job_id=job_id,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        try:
            # 1. Parse into raw units
            if ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read().strip()
                raw_units = [{
                    "text": text_content if text_content else f"Document {source_title}",
                    "page": 1,
                    "type": "text",
                    "ocr_provider_used": None,
                    "token_count": len(text_content.split()),
                }]
                source.page_count = 1
            elif kind == SourceKind.pdf:
                raw_units = parse_pdf(file_path, ocr_provider=ocr_provider)
                source.page_count = max([u.get("page", 1) for u in raw_units], default=1)
            elif kind == SourceKind.pptx:
                raw_units = parse_pptx(file_path)
                source.page_count = max([u.get("slide_no", 1) for u in raw_units], default=1)
            elif kind in [SourceKind.video, SourceKind.audio]:
                raw_units = parse_video_audio(file_path)
                source.duration_secs = max([u.get("ts_end", 0.0) for u in raw_units], default=0.0)
            elif kind == SourceKind.image:
                raw_units = parse_image(file_path, ocr_provider=ocr_provider)
                source.page_count = 1
            else:
                raw_units = parse_pdf(file_path, ocr_provider=ocr_provider)

            if not raw_units:
                raw_units = [{
                    "text": f"Document content from {source_title}",
                    "page": 1,
                    "type": "text",
                    "ocr_provider_used": None,
                }]

            # 2. Persist Units to DB
            db_units: List[Unit] = []
            for u_data in raw_units:
                unit_type = UnitType(u_data.get("type", "text"))
                unit = Unit(
                    source_id=source.id,
                    type=unit_type,
                    text=u_data["text"],
                    page=u_data.get("page"),
                    slide_no=u_data.get("slide_no"),
                    ts_start=u_data.get("ts_start"),
                    ts_end=u_data.get("ts_end"),
                    figure_path=u_data.get("figure_path"),
                    lang=u_data.get("lang", "en"),
                    token_count=u_data.get("token_count", len(u_data["text"].split())),
                    ocr_provider_used=u_data.get("ocr_provider_used"),
                )
                db.add(unit)
                db_units.append(unit)

            db.commit()
            for u in db_units:
                db.refresh(u)

            # 3. Generate embeddings and upsert to vector store
            if llm_client and vector_store:
                texts = [u.text for u in db_units]
                embeddings = llm_client.embed(texts)
                vectors_to_upsert: List[Dict[str, Any]] = []

                for u, emb in zip(db_units, embeddings):
                    vector_id = f"unit_{u.id}"
                    u.embedding_id = vector_id

                    meta = {
                        "unit_id": u.id,
                        "source_id": source.id,
                        "source_title": source.title,
                        "type": u.type.value,
                        "page": u.page,
                        "slide_no": u.slide_no,
                        "ts_start": u.ts_start,
                        "ts_end": u.ts_end,
                        "text": u.text[:500],
                    }
                    vectors_to_upsert.append({
                        "id": vector_id,
                        "values": emb,
                        "metadata": meta,
                    })

                    # Track in VectorRef
                    db.add(VectorRef(
                        owner_id=u.id,
                        kind="unit",
                        vector_id=vector_id,
                        namespace="units",
                    ))

                    # Cache embedding blob locally in SQLite (float16 bytes)
                    raw_blob = struct.pack(f"{len(emb)}e", *emb)
                    db.add(EmbeddingCache(
                        owner_id=u.id,
                        kind="unit",
                        blob=raw_blob,
                        dim=len(emb),
                        model="local-embed",
                    ))

                vector_store.upsert(vectors_to_upsert, namespace="units")
                db.commit()

            source.status = "ready"
            db.commit()
            db.refresh(source)
            return source

        except Exception as exc:
            db.rollback()
            source.status = "failed"
            db.commit()
            logger.error("Ingestion failed for source %d: %s", source.id, exc)
            raise AppError(f"Ingestion processing failed: {exc}")

    @staticmethod
    def process_youtube_or_video_url(
        db: Session,
        url: str,
        title: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        vector_store: Optional[VectorStore] = None,
        auto_build_knowledge: bool = True,
        job_id: Optional[int] = None,
    ) -> Source:
        """Parse and ingest a YouTube video or external video URL into timestamped lecture units."""
        clean_url = url.strip()
        url_hash = hashlib.sha256(clean_url.lower().encode("utf-8")).hexdigest()

        # Check deduplication
        existing = db.query(Source).filter(Source.file_hash == url_hash).first()
        if existing and existing.status == "ready":
            logger.info("Video URL already ingested: %s (source id %d)", clean_url, existing.id)
            return existing

        # Extract metadata and timestamped transcript units
        stt_provider = getattr(settings, "INGEST_STT_PROVIDER", "faster-whisper")
        metadata, raw_units = parse_youtube_video(clean_url, stt_provider=stt_provider)

        source_title = title or metadata.get("title") or "Video Lecture"
        duration_secs = metadata.get("duration_secs", 0.0)

        source = existing or Source(
            title=source_title,
            kind=SourceKind.video,
            file_path=clean_url,
            file_hash=url_hash,
            file_size=int(duration_secs * 1024) if duration_secs else 1024,
            duration_secs=duration_secs,
            status="processing",
            job_id=job_id,
        )
        if not existing:
            db.add(source)
            db.commit()
            db.refresh(source)
        else:
            source.status = "processing"
            source.title = source_title
            source.duration_secs = duration_secs
            db.commit()

        try:
            # Delete old units if re-processing existing
            if existing:
                db.query(Unit).filter(Unit.source_id == source.id).delete()
                db.commit()

            # Persist timestamped units
            db_units: List[Unit] = []
            for u_data in raw_units:
                unit = Unit(
                    source_id=source.id,
                    type=UnitType.transcript,
                    text=u_data["text"],
                    page=None,
                    slide_no=None,
                    ts_start=u_data.get("ts_start"),
                    ts_end=u_data.get("ts_end"),
                    lang=u_data.get("lang", "en"),
                    token_count=u_data.get("token_count", len(u_data["text"].split())),
                    ocr_provider_used=None,
                )
                db.add(unit)
                db_units.append(unit)

            db.commit()
            for u in db_units:
                db.refresh(u)

            # Generate embeddings and upsert to vector store
            if llm_client and vector_store:
                texts = [u.text for u in db_units]
                embeddings = llm_client.embed(texts)
                vectors_to_upsert: List[Dict[str, Any]] = []

                for u, emb in zip(db_units, embeddings):
                    vector_id = f"unit_{u.id}"
                    u.embedding_id = vector_id

                    meta = {
                        "unit_id": u.id,
                        "source_id": source.id,
                        "source_title": source.title,
                        "type": "transcript",
                        "ts_start": u.ts_start,
                        "ts_end": u.ts_end,
                        "video_url": clean_url,
                        "text": u.text[:500],
                    }
                    vectors_to_upsert.append({
                        "id": vector_id,
                        "values": emb,
                        "metadata": meta,
                    })

                    db.add(VectorRef(
                        owner_id=u.id,
                        kind="unit",
                        vector_id=vector_id,
                        namespace="units",
                    ))

                    raw_blob = struct.pack(f"{len(emb)}e", *emb)
                    db.add(EmbeddingCache(
                        owner_id=u.id,
                        kind="unit",
                        blob=raw_blob,
                        dim=len(emb),
                        model="local-embed",
                    ))

                vector_store.upsert(vectors_to_upsert, namespace="units")
                db.commit()

            source.status = "ready"
            db.commit()
            db.refresh(source)

            # Automatically build or update Knowledge DAG if requested
            if auto_build_knowledge and llm_client:
                try:
                    from app.modules.knowledge.service import KnowledgeService
                    KnowledgeService.build_knowledge_base(db, llm_client, vector_store=vector_store)
                except Exception as k_exc:
                    logger.warning("Auto knowledge base update warning: %s", k_exc)

            return source

        except Exception as exc:
            db.rollback()
            source.status = "failed"
            db.commit()
            logger.error("Video ingestion failed for source %d: %s", source.id, exc)
            raise AppError(f"Video ingestion processing failed: {exc}")

    @staticmethod
    def get_source(db: Session, source_id: int) -> Source:

        source = db.get(Source, source_id)
        if not source:
            raise NotFoundError(f"Source {source_id} not found")
        return source

    @staticmethod
    def list_sources(db: Session, skip: int = 0, limit: int = 50) -> List[Source]:
        return db.query(Source).offset(skip).limit(limit).all()

    @staticmethod
    def delete_source(
        db: Session,
        source_id: int,
        vector_store: Optional[VectorStore] = None,
    ) -> bool:
        source = db.get(Source, source_id)
        if not source:
            raise NotFoundError(f"Source {source_id} not found")

        # Delete vectors from vector store if vector_store available
        if vector_store:
            vector_refs = db.query(VectorRef).filter(
                VectorRef.owner_id.in_([u.id for u in source.units]),
                VectorRef.kind == "unit",
            ).all()
            if vector_refs:
                vector_ids = [vr.vector_id for vr in vector_refs]
                vector_store.delete(ids=vector_ids, namespace="units")

        db.delete(source)
        db.commit()
        return True

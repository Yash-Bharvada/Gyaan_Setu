"""Ingestion API Router.

Endpoints for uploading documents, listing sources, and monitoring ingestion jobs.
"""
from __future__ import annotations

import os
import shutil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, get_llm, get_ocr_provider, get_vector_store
from app.llm.base import LLMClient
from app.models import Source, SourceKind, Unit
from app.modules.ingestion.jobs import JobService
from app.modules.ingestion.service import IngestionService
from app.vectorstore.base import VectorStore

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    type: str
    text: str
    page: Optional[int] = None
    slide_no: Optional[int] = None
    ts_start: Optional[float] = None
    ts_end: Optional[float] = None
    lang: Optional[str] = "en"
    token_count: Optional[int] = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    kind: str
    file_path: Optional[str] = None
    file_size: int
    status: str
    page_count: Optional[int] = None
    duration_secs: Optional[float] = None
    units: Optional[List[UnitOut]] = None


class RawTextInput(BaseModel):
    title: str
    text: str
    lang: Optional[str] = "en"


class YouTubeIngestInput(BaseModel):
    url: str
    title: Optional[str] = None
    async_mode: Optional[bool] = False
    auto_build_knowledge: Optional[bool] = True


def _run_background_youtube_ingest(
    url: str,
    title: Optional[str],
    job_id: int,
):
    from app.core.db import SessionLocal
    from app.llm.factory import get_llm
    from app.vectorstore.local_store import LocalVectorStore

    db = SessionLocal()
    try:
        JobService.start(db, job_id)
        llm = get_llm()
        vstore = LocalVectorStore()
        source = IngestionService.process_youtube_or_video_url(
            db=db,
            url=url,
            title=title,
            llm_client=llm,
            vector_store=vstore,
            auto_build_knowledge=True,
            job_id=job_id,
        )
        JobService.complete(db, job_id, result=f'{{"source_id": {source.id}}}')
    except Exception as exc:
        JobService.fail(db, job_id, error=str(exc))
    finally:
        db.close()


def _run_background_ingest(
    file_path: str,
    title: str,
    job_id: int,
):

    from app.core.db import SessionLocal
    from app.llm.factory import get_llm
    from app.ocr.mock import MockOCRProvider
    from app.vectorstore.local_store import LocalVectorStore

    db = SessionLocal()
    try:
        JobService.start(db, job_id)
        llm = get_llm()
        vstore = LocalVectorStore()
        ocr = MockOCRProvider()
        source = IngestionService.process_file(
            db=db,
            file_path=file_path,
            title=title,
            llm_client=llm,
            vector_store=vstore,
            ocr_provider=ocr,
            job_id=job_id,
        )
        JobService.complete(db, job_id, result=f'{{"source_id": {source.id}}}')
    except Exception as exc:
        JobService.fail(db, job_id, error=str(exc))
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    async_mode: bool = Form(True),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
    ocr = Depends(get_ocr_provider),
):
    """Upload a file (PDF, PPTX, Video, Image) for multimodal ingestion."""
    uploads_dir = os.path.join(settings.DATA_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    dest_path = os.path.join(uploads_dir, file.filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    source_title = title or file.filename

    if async_mode:
        job = JobService.create(db, kind="ingest", message=f"Ingesting {file.filename}")
        background_tasks.add_task(_run_background_ingest, dest_path, source_title, job.id)
        return {"status": "accepted", "job_id": job.id, "message": "Ingestion started in background"}
    else:
        source = IngestionService.process_file(
            db=db,
            file_path=dest_path,
            title=source_title,
            llm_client=llm,
            vector_store=vstore,
            ocr_provider=ocr,
        )
        return {"status": "completed", "source_id": source.id, "title": source.title}


@router.post("/text", response_model=Dict[str, Any])
def ingest_raw_text(
    payload: RawTextInput,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
    ocr = Depends(get_ocr_provider),
):
    """Directly ingest a raw text block."""
    uploads_dir = os.path.join(settings.DATA_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_name = f"{payload.title.lower().replace(' ', '_')}.txt"
    dest_path = os.path.join(uploads_dir, file_name)

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(payload.text)

    source = IngestionService.process_file(
        db=db,
        file_path=dest_path,
        title=payload.title,
        llm_client=llm,
        vector_store=vstore,
        ocr_provider=ocr,
    )
    return {"status": "completed", "source_id": source.id, "title": source.title, "units_count": len(source.units)}


@router.post("/youtube", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def ingest_youtube_video(
    payload: YouTubeIngestInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
):
    """Ingest a YouTube video or video URL, extracting metadata and timestamped transcript units."""
    if payload.async_mode:
        job = JobService.create(db, kind="ingest", message=f"Ingesting YouTube video {payload.url}")
        background_tasks.add_task(_run_background_youtube_ingest, payload.url, payload.title, job.id)
        return {
            "status": "accepted",
            "job_id": job.id,
            "message": "YouTube video ingestion started in background",
        }
    else:
        source = IngestionService.process_youtube_or_video_url(
            db=db,
            url=payload.url,
            title=payload.title,
            llm_client=llm,
            vector_store=vstore,
            auto_build_knowledge=payload.auto_build_knowledge if payload.auto_build_knowledge is not None else True,
        )
        return {
            "status": "completed",
            "source_id": source.id,
            "title": source.title,
            "kind": source.kind.value,
            "units_count": len(source.units),
            "duration_secs": source.duration_secs,
            "message": f"Successfully parsed video lecture with {len(source.units)} timestamped lecture segments.",
        }


@router.post("/video-url", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def ingest_video_url(
    payload: YouTubeIngestInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
):
    """Alias for ingesting any YouTube video or external video lecture URL."""
    return ingest_youtube_video(
        payload=payload,
        background_tasks=background_tasks,
        db=db,
        llm=llm,
        vstore=vstore,
    )



@router.get("/sources", response_model=List[SourceOut])
def list_sources(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all ingested sources."""
    return IngestionService.list_sources(db, skip=skip, limit=limit)


@router.get("/sources/{source_id}", response_model=SourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """Get single source details with all its units."""
    return IngestionService.get_source(db, source_id)


@router.delete("/sources/{source_id}")
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    vstore: VectorStore = Depends(get_vector_store),
):
    """Delete source and its vector embeddings."""
    IngestionService.delete_source(db, source_id, vector_store=vstore)
    return {"status": "deleted", "source_id": source_id}


@router.get("/jobs/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get status of an ingestion background job."""
    job = JobService.get(db, job_id)
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status.value,
        "progress": job.progress,
        "message": job.message,
        "result": job.result,
        "error": job.error,
    }

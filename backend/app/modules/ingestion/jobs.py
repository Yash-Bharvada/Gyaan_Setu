"""
JobService — thin wrapper around the `jobs` table.

All background work creates a job row first, then updates it as it runs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import JobNotFoundError
from app.models import Job, JobStatus


class JobService:

    @staticmethod
    def create(db: Session, kind: str, message: str = "queued") -> Job:
        job = Job(kind=kind, status=JobStatus.pending, message=message)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def start(db: Session, job_id: int) -> Job:
        job = db.get(Job, job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        job.status = JobStatus.running
        job.started_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def update_progress(db: Session, job_id: int, progress: float, message: str = "") -> None:
        job = db.get(Job, job_id)
        if not job:
            return
        job.progress = min(1.0, max(0.0, progress))
        if message:
            job.message = message
        db.commit()

    @staticmethod
    def complete(db: Session, job_id: int, result: Optional[str] = None) -> Job:
        job = db.get(Job, job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        job.status = JobStatus.completed
        job.progress = 1.0
        job.completed_at = datetime.utcnow()
        if result:
            job.result = result
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def fail(db: Session, job_id: int, error: str) -> Job:
        job = db.get(Job, job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        job.status = JobStatus.failed
        job.error = error
        job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get(db: Session, job_id: int) -> Job:
        job = db.get(Job, job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job

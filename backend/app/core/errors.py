"""Custom exceptions and FastAPI error handlers producing the standard envelope."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ── Error envelope ──────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


def error_response(
    code: str,
    message: str,
    status_code: int,
    details: Any | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


# ── Domain exceptions ────────────────────────────────────────────────────────

class StudyCompanionError(Exception):
    """Base for all application errors."""

    http_status: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, details: Any | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(StudyCompanionError):
    http_status = 404
    code = "not_found"


class ValidationError(StudyCompanionError):
    http_status = 422
    code = "validation_error"


class UnsupportedFileTypeError(StudyCompanionError):
    http_status = 415
    code = "unsupported_file_type"


class FileTooLargeError(StudyCompanionError):
    http_status = 413
    code = "file_too_large"


class QuotaExceededError(StudyCompanionError):
    http_status = 429
    code = "quota_exceeded"


class LLMError(StudyCompanionError):
    http_status = 502
    code = "llm_error"


class VectorStoreError(StudyCompanionError):
    http_status = 502
    code = "vector_store_error"


class OCRError(StudyCompanionError):
    http_status = 502
    code = "ocr_error"


class JobNotFoundError(NotFoundError):
    code = "job_not_found"


class DuplicateUploadError(StudyCompanionError):
    http_status = 409
    code = "duplicate_upload"


# ── FastAPI handlers ─────────────────────────────────────────────────────────

def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(StudyCompanionError)
    async def handle_domain_error(request: Request, exc: StudyCompanionError):  # noqa: ARG001
        return error_response(exc.code, exc.message, exc.http_status, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):  # noqa: ARG001
        return error_response(
            "validation_error",
            "Request validation failed",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(),
        )

    @app.exception_handler(404)
    async def handle_404(request: Request, exc):  # noqa: ARG001
        return error_response("not_found", "Resource not found", 404)

    @app.exception_handler(Exception)
    async def handle_generic(request: Request, exc: Exception):  # noqa: ARG001
        return error_response("internal_error", "An unexpected error occurred", 500)

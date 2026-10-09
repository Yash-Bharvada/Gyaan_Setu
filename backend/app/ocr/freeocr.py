"""
freeocr.ai REST OCR provider.

API (from https://freeocr.ai/api):
  POST https://freeocr.ai/api/v1/platform/ocr
  Header: Authorization: Bearer focr_<key>
  Body:   multipart/form-data  field "image" (PNG / JPEG / WEBP)
  Response: JSON with a text field.

Quota guard: calls are counted via UsageLedger; once FREEOCR_MAX_CALLS is
reached the factory switches to TesseractProvider automatically.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.core.errors import OCRError
from app.ocr.base import OCRProvider

logger = logging.getLogger(__name__)

_ENDPOINT = "https://freeocr.ai/api/v1/platform/ocr"


class FreeOCRProvider(OCRProvider):

    provider_name = "freeocr.ai"

    def ocr_image(self, image_bytes: bytes) -> str:
        if not settings.FREEOCR_API_KEY:
            raise OCRError("FREEOCR_API_KEY is not set")
        try:
            resp = httpx.post(
                _ENDPOINT,
                headers={"Authorization": f"Bearer {settings.FREEOCR_API_KEY}"},
                files={"image": ("image.png", image_bytes, "image/png")},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            # The API returns a text field (markdown or plain text)
            return data.get("text") or data.get("markdown") or ""
        except httpx.HTTPStatusError as exc:
            raise OCRError(f"freeocr.ai HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except Exception as exc:
            raise OCRError(f"freeocr.ai request failed: {exc}") from exc

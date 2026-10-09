"""Tesseract local OCR fallback."""
from __future__ import annotations

import io
import logging

from app.core.errors import OCRError
from app.ocr.base import OCRProvider

logger = logging.getLogger(__name__)


class TesseractProvider(OCRProvider):

    provider_name = "tesseract"

    def __init__(self, lang: str = "eng+hin"):
        self._lang = lang

    def ocr_image(self, image_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(img, lang=self._lang)
        except ImportError as exc:
            raise OCRError(
                "pytesseract or Pillow not installed; run: pip install pytesseract Pillow"
            ) from exc
        except Exception as exc:
            raise OCRError(f"Tesseract OCR failed: {exc}") from exc

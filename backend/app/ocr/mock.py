"""MockOCR for tests — never calls any external service."""
from __future__ import annotations

import hashlib

from app.ocr.base import OCRProvider


class MockOCR(OCRProvider):
    provider_name = "mock_ocr"

    def ocr_image(self, image_bytes: bytes) -> str:
        digest = hashlib.md5(image_bytes).hexdigest()[:8]
        return f"[MOCK OCR TEXT for image hash={digest}]"


def get_ocr_factory(*, force_mock: bool = False) -> OCRProvider:
    """
    Return the appropriate OCR provider.

    Priority:
    1. MockOCR when *force_mock* is True (tests).
    2. FreeOCRProvider while the ledger is under FREEOCR_MAX_CALLS and the key is set.
    3. TesseractProvider otherwise.
    """
    if force_mock:
        return MockOCR()

    from app.core.config import settings
    from app.quota.ledger import UsageLedger

    if settings.FREEOCR_API_KEY:
        ledger = UsageLedger.instance()
        used = ledger.total("freeocr.ai", "calls")
        if used < settings.FREEOCR_MAX_CALLS:
            from app.ocr.freeocr import FreeOCRProvider
            return FreeOCRProvider()

    from app.ocr.tesseract import TesseractProvider
    return TesseractProvider()

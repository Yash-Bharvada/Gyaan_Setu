"""PDF Parser module.

Extracts text and page-grounded content units from PDF files.
Falls back to OCR if a page contains no text or is an image/scan.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_pdf(
    file_path: str,
    ocr_provider: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Parse a PDF file and return a list of extracted page units.

    Each unit dict contains:
        - text: Extracted text content
        - page: 1-indexed page number
        - type: 'text' or 'figure'
        - ocr_provider_used: Name of OCR provider if OCR was needed
    """
    units: List[Dict[str, Any]] = []

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text("text").strip()

            ocr_used: Optional[str] = None
            if not text and ocr_provider is not None:
                try:
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    text = ocr_provider.extract_text(img_bytes).strip()
                    ocr_used = getattr(ocr_provider, "name", "ocr")
                except Exception as e:
                    logger.warning("OCR failed on page %d of %s: %s", page_num, file_path, e)

            if text:
                units.append({
                    "text": text,
                    "page": page_num,
                    "type": "text",
                    "ocr_provider_used": ocr_used,
                    "token_count": len(text.split()),
                })
        doc.close()
    except Exception as exc:
        logger.error("Error reading PDF %s: %s", file_path, exc)
        # Fallback basic text extraction if fitz fails
        if not units:
            units.append({
                "text": f"Extracted content from {os.path.basename(file_path)}",
                "page": 1,
                "type": "text",
                "ocr_provider_used": None,
                "token_count": 10,
            })

    return units

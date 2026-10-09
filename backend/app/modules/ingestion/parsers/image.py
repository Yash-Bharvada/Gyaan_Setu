"""Image Parser module.

Extracts text from scanned diagrams, notes, and photos using the configured OCR provider.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_image(
    file_path: str,
    ocr_provider: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Extract text from an image file.

    Returns a list containing unit dict:
        - text: Extracted text
        - type: 'figure' or 'text'
        - figure_path: local path to the image
        - ocr_provider_used: name of OCR provider used
    """
    text = ""
    ocr_used = None

    try:
        with open(file_path, "rb") as f:
            image_bytes = f.read()

        if ocr_provider is not None:
            text = ocr_provider.extract_text(image_bytes).strip()
            ocr_used = getattr(ocr_provider, "name", "ocr")
    except Exception as exc:
        logger.warning("Image OCR failed for %s: %s", file_path, exc)

    if not text:
        text = f"Image content extracted from {os.path.basename(file_path)}"

    return [
        {
            "text": text,
            "type": "figure",
            "figure_path": file_path,
            "ocr_provider_used": ocr_used,
            "token_count": len(text.split()),
        }
    ]

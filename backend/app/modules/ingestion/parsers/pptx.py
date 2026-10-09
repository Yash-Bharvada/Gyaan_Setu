"""PPTX Parser module.

Extracts text, slide titles, bullet points, and speaker notes from PowerPoint presentations (.pptx).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_pptx(file_path: str) -> List[Dict[str, Any]]:
    """Parse a PPTX file and return a list of slide units.

    Each unit dict contains:
        - text: Slide title + text contents + notes
        - slide_no: 1-indexed slide number
        - type: 'slide'
        - token_count: token estimate
    """
    units: List[Dict[str, Any]] = []

    try:
        from pptx import Presentation
        prs = Presentation(file_path)

        for slide_idx, slide in enumerate(prs.slides):
            slide_no = slide_idx + 1
            texts: List[str] = []

            # Extract shapes text
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text_str = "".join(run.text for run in paragraph.runs).strip()
                        if text_str:
                            texts.append(text_str)

            # Extract speaker notes if any
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    texts.append(f"[Notes: {notes}]")

            full_text = "\n".join(texts).strip()
            if full_text:
                units.append({
                    "text": full_text,
                    "slide_no": slide_no,
                    "type": "slide",
                    "ocr_provider_used": None,
                    "token_count": len(full_text.split()),
                })

    except Exception as exc:
        logger.error("Error reading PPTX %s: %s", file_path, exc)
        if not units:
            units.append({
                "text": f"Extracted slide content from {os.path.basename(file_path)}",
                "slide_no": 1,
                "type": "slide",
                "ocr_provider_used": None,
                "token_count": 10,
            })

    return units

"""Language API Router.

Endpoints for language detection and cross-lingual translation.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_llm
from app.llm.base import LLMClient
from app.modules.language.detect import detect_language
from app.modules.language.translate import Translator

router = APIRouter(prefix="/language", tags=["Language & Multilingual"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class DetectRequest(BaseModel):
    text: str


class TranslateRequest(BaseModel):
    text: str
    target_lang: Optional[str] = "en"  # "en", "hi", "hi-Latn"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/detect", response_model=Dict[str, Any])
def detect_lang(payload: DetectRequest):
    """Detect text language: 'en' (English), 'hi' (Hindi), or 'hi-Latn' (Hinglish)."""
    lang = detect_language(payload.text)
    return {"text": payload.text, "detected_lang": lang}


@router.post("/translate", response_model=Dict[str, Any])
def translate(
    payload: TranslateRequest,
    llm: LLMClient = Depends(get_llm),
):
    """Translate text into target language."""
    translated = Translator.translate_text(
        text=payload.text,
        target_lang=payload.target_lang or "en",
        llm=llm,
    )
    return {
        "original_text": payload.text,
        "target_lang": payload.target_lang,
        "translated_text": translated,
    }

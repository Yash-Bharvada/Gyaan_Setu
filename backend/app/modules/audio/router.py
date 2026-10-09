"""Audio API Router.

Endpoints for Speech-to-Text (STT), Text-to-Speech (TTS), and multimodal Voice Tutoring.
"""
from __future__ import annotations

import base64
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_llm, get_vector_store
from app.llm.base import LLMClient
from app.modules.audio.stt import STTService
from app.modules.audio.tts import TTSService
from app.modules.tutor.service import TutorService
from app.vectorstore.base import VectorStore

router = APIRouter(prefix="/audio", tags=["Audio & Voice"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class SynthesizeRequest(BaseModel):
    text: str
    target_language_code: Optional[str] = "hi-IN"
    speaker_gender: Optional[str] = "female"
    speaker: Optional[str] = None
    pace: Optional[float] = 1.0


class PodcastTurn(BaseModel):
    speaker: str = "host1"
    speaker_name: Optional[str] = "Host"
    text: str


class PodcastSynthesizeRequest(BaseModel):
    dialogue: list[PodcastTurn]
    language: Optional[str] = "en"
    host1_voice: Optional[str] = "meera"
    host2_voice: Optional[str] = "arvind"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/transcribe", response_model=Dict[str, Any])
async def transcribe_audio(
    file: UploadFile = File(...),
    language_code: Optional[str] = Form("hi-IN"),
):
    """Transcribe uploaded audio file to text."""
    audio_bytes = await file.read()
    transcript = STTService.transcribe(audio_bytes=audio_bytes, language_code=language_code)
    return {"transcript": transcript, "filename": file.filename}


@router.post("/synthesize")
def synthesize_speech(payload: SynthesizeRequest):
    """Synthesize text into speech audio bytes using Sarvam AI (or local neural fallback)."""
    audio_bytes = TTSService.synthesize(
        text=payload.text,
        target_language_code=payload.target_language_code,
        speaker_gender=payload.speaker_gender,
        speaker=payload.speaker,
        pace=payload.pace,
    )
    media_type = "audio/wav" if audio_bytes.startswith(b"RIFF") else "audio/mpeg"
    filename = "speech.wav" if audio_bytes.startswith(b"RIFF") else "speech.mp3"
    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.post("/synthesize-podcast")
def synthesize_podcast(payload: PodcastSynthesizeRequest):
    """Synthesize 2-host podcast conversation with multi-voice Sarvam AI audio merging."""
    dialogue_dicts = [turn.model_dump() for turn in payload.dialogue]
    audio_bytes = TTSService.synthesize_podcast(
        dialogue=dialogue_dicts,
        language=payload.language or "en",
        host1_voice=payload.host1_voice or "priya",
        host2_voice=payload.host2_voice or "kabir",
    )
    media_type = "audio/wav" if audio_bytes.startswith(b"RIFF") else "audio/mpeg"
    filename = "podcast.wav" if audio_bytes.startswith(b"RIFF") else "podcast.mp3"
    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )




@router.post("/voice-chat", response_model=Dict[str, Any])
async def voice_tutoring_chat(
    file: UploadFile = File(...),
    session_id: Optional[int] = Form(None),
    language_code: Optional[str] = Form("hi-IN"),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
):
    """End-to-end voice tutoring: Voice Input -> STT -> Grounded RAG Tutor -> TTS Audio Output."""
    audio_bytes = await file.read()

    # 1. Transcribe voice question
    query_text = STTService.transcribe(audio_bytes=audio_bytes, language_code=language_code)

    # 2. Get grounded tutor reply
    sid = session_id or 0
    tutor_res = TutorService.answer_query(
        db=db,
        session_id=sid,
        query=query_text,
        llm=llm,
        vector_store=vstore,
    )

    # 3. Synthesize voice response
    reply_audio_bytes = TTSService.synthesize(
        text=tutor_res["reply"],
        target_language_code=language_code,
    )
    b64_audio = base64.b64encode(reply_audio_bytes).decode("utf-8")

    return {
        "session_id": tutor_res["session_id"],
        "user_query_transcript": query_text,
        "tutor_reply_text": tutor_res["reply"],
        "citations": tutor_res["citations"],
        "grounded": tutor_res["grounded"],
        "audio_base64": b64_audio,
    }

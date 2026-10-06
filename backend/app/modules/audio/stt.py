"""Speech-to-Text (STT) module.

Supports Sarvam AI Indic STT (with budget guard), faster-whisper local model, and offline mock STT.
"""
from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional

import httpx

from app.core.config import settings
from app.core.errors import QuotaExceededError
from app.quota.guard import get_sarvam_guard

logger = logging.getLogger(__name__)


class STTService:
    @staticmethod
    def transcribe(
        audio_bytes: bytes,
        language_code: Optional[str] = "hi-IN",
        provider: Optional[str] = None,
    ) -> str:
        """Transcribe audio bytes to text using Sarvam AI or local faster-whisper."""
        chosen_provider = provider or getattr(settings, "QA_STT_PROVIDER", "faster-whisper")
        sarvam_key = getattr(settings, "SARVAM_API_KEY", "")

        # 1. Try Sarvam AI STT if key available and requested
        if (chosen_provider == "sarvam" or not chosen_provider) and sarvam_key:
            guard = get_sarvam_guard()
            if not guard.is_over():
                try:
                    guard.check()
                    url = "https://api.sarvam.ai/speech-to-text"
                    headers = {"api-subscription-key": sarvam_key}
                    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                    data = {"model": "saaras:v1", "language_code": language_code or "hi-IN"}

                    with httpx.Client(timeout=30.0) as client:
                        resp = client.post(url, headers=headers, files=files, data=data)
                        if resp.status_code == 200:
                            transcript = resp.json().get("transcript", "")
                            guard.record(amount=0.10, est_cost=0.10)  # Record 0.10 INR
                            return transcript
                except Exception as exc:
                    logger.warning("Sarvam STT failed: %s. Falling back to local whisper.", exc)

        # 2. Local faster-whisper fallback
        try:
            from faster_whisper import WhisperModel
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, info = model.transcribe(tmp_path, beam_size=1)
                text = " ".join([seg.text for seg in segments]).strip()
                return text if text else "Transcribed speech query."
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as exc:
            logger.warning("Local whisper STT error: %s. Using mock transcription.", exc)

        # 3. Mock fallback
        return "Can you explain the main concepts and formulas in this chapter?"

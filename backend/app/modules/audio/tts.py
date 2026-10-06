"""Text-to-Speech (TTS) module.

Supports Sarvam AI Indic TTS (with budget guard), Edge-TTS, gTTS, and mock audio generation.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
from typing import Optional

import httpx

from app.core.config import settings
from app.quota.guard import get_sarvam_guard

logger = logging.getLogger(__name__)


class TTSService:
    @staticmethod
    def synthesize(
        text: str,
        target_language_code: Optional[str] = "hi-IN",
        speaker_gender: Optional[str] = "female",
    ) -> bytes:
        """Synthesize text into speech audio bytes (MP3/WAV)."""
        clean_text = text.strip()
        if not clean_text:
            return b""

        sarvam_key = getattr(settings, "SARVAM_API_KEY", "")

        # 1. Try Sarvam AI TTS
        if sarvam_key:
            guard = get_sarvam_guard()
            if not guard.is_over():
                try:
                    guard.check()
                    url = "https://api.sarvam.ai/text-to-speech"
                    headers = {
                        "api-subscription-key": sarvam_key,
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "inputs": [clean_text[:500]],
                        "target_language_code": target_language_code or "hi-IN",
                        "speaker": "meera" if speaker_gender == "female" else "arvind",
                        "model": "bulbul:v1",
                    }
                    with httpx.Client(timeout=30.0) as client:
                        resp = client.post(url, headers=headers, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            audios = data.get("audios", [])
                            if audios:
                                audio_bytes = base64.b64decode(audios[0])
                                guard.record(amount=0.15, est_cost=0.15)
                                return audio_bytes
                except Exception as exc:
                    logger.warning("Sarvam TTS error: %s. Falling back to local TTS.", exc)

        # 2. Try Edge-TTS / gTTS
        try:
            from gtts import gTTS
            lang_code = "hi" if "hi" in (target_language_code or "") else "en"
            tts = gTTS(text=clean_text[:400], lang=lang_code, slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tts.save(tmp.name)
                tmp_path = tmp.name

            try:
                with open(tmp_path, "rb") as f:
                    return f.read()
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as exc:
            logger.warning("gTTS local synthesis error: %s. Using synthetic audio header.", exc)

        # 3. Fallback dummy WAV header (44-byte standard valid WAV file)
        # RIFF header for valid silent wav
        wav_header = (
            b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
            b"D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        )
        return wav_header

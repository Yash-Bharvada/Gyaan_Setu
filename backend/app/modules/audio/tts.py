"""Text-to-Speech (TTS) module.

Supports Sarvam AI Indic TTS (with budget guard), Edge-TTS, gTTS, and mock audio generation.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
import tempfile
from typing import List, Optional

import httpx

from app.core.config import settings
from app.quota.guard import get_elevenlabs_guard, get_sarvam_guard

logger = logging.getLogger(__name__)


class TTSService:
    @staticmethod
    def _synthesize_elevenlabs(
        text: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2",
    ) -> Optional[bytes]:
        """Synthesize via ElevenLabs Free Tier with local caching & strict quota guard."""
        api_key = getattr(settings, "ELEVENLABS_API_KEY", "") or os.environ.get("ELEVENLABS_API_KEY", "")
        if not api_key:
            return None

        # Check local disk cache first (never wastes characters)
        cache_dir = os.path.join(settings.DATA_DIR, "audio_cache")
        os.makedirs(cache_dir, exist_ok=True)
        key_str = f"elevenlabs:{voice_id}:{model_id}:{text.strip()}"
        cache_file = os.path.join(cache_dir, f"{hashlib.sha256(key_str.encode()).hexdigest()}.mp3")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    return f.read()
            except Exception:
                pass

        # Free tier character guard (10,000 monthly limit)
        guard = get_elevenlabs_guard()
        if guard.is_over():
            logger.warning("ElevenLabs Free Tier character cap reached (10,000 chars). Falling back.")
            return None

        # Trim text to prevent overage
        trimmed_text = text.strip()[:400]
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": trimmed_text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200 and resp.content:
                    guard.record(amount=len(trimmed_text), est_cost=0.0)
                    try:
                        with open(cache_file, "wb") as f:
                            f.write(resp.content)
                    except Exception:
                        pass
                    return resp.content
                else:
                    logger.warning("ElevenLabs status %s: %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("ElevenLabs error: %s", exc)

        return None

    @staticmethod
    def synthesize(
        text: str,
        target_language_code: Optional[str] = "hi-IN",
        speaker_gender: Optional[str] = "female",
        speaker: Optional[str] = None,
        pace: Optional[float] = 1.0,
    ) -> bytes:
        """Synthesize text into speech audio bytes (MP3/WAV)."""
        clean_text = text.strip()
        if not clean_text:
            return b""

        # Determine speaker persona
        chosen_speaker = (speaker or "").lower().strip()
        if not chosen_speaker or chosen_speaker in ["meera", "female", "host1"]:
            chosen_speaker = "priya"
        elif chosen_speaker in ["arvind", "male", "host2"]:
            chosen_speaker = "kabir"

        # 1. Try ElevenLabs Free Tier (high-fidelity multilingual neural voice)
        tts_provider = getattr(settings, "TTS_PROVIDER", "elevenlabs")
        elevenlabs_key = getattr(settings, "ELEVENLABS_API_KEY", "") or os.environ.get("ELEVENLABS_API_KEY", "")
        if (tts_provider == "elevenlabs" or elevenlabs_key) and elevenlabs_key:
            voice_id = getattr(settings, "ELEVENLABS_VOICE_FEMALE", "EXAVITQu4vr4xnSDxMaL")
            if (speaker_gender or "").lower() == "male" or chosen_speaker in ["kabir", "arvind", "male", "host2"]:
                voice_id = getattr(settings, "ELEVENLABS_VOICE_MALE", "JBFqnCBsd6RMkjVDRZzb")
            elif chosen_speaker in ["priya", "meera", "female", "host1"]:
                voice_id = getattr(settings, "ELEVENLABS_VOICE_FEMALE", "EXAVITQu4vr4xnSDxMaL")

            audio_mp3 = TTSService._synthesize_elevenlabs(
                text=clean_text,
                voice_id=voice_id,
                model_id=getattr(settings, "ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
            )
            if audio_mp3:
                return audio_mp3

        sarvam_key = getattr(settings, "SARVAM_API_KEY", "") or os.environ.get("SARVAM_API_KEY", "")

        # Normalize language code to BCP-47
        lang_str = (target_language_code or "hi-IN").lower()
        if "hi" in lang_str:
            bcp47_lang = "hi-IN"
        elif "en" in lang_str:
            bcp47_lang = "en-IN"
        else:
            bcp47_lang = target_language_code or "hi-IN"

        # 1. Try Sarvam AI TTS (Bulbul v3)
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
                        "target_language_code": bcp47_lang,
                        "speaker": chosen_speaker,
                        "model": "bulbul:v3",
                        "enable_preprocessing": True,
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
                        else:
                            logger.warning(
                                "Sarvam TTS status %s: %s", resp.status_code, resp.text[:200]
                            )
                except Exception as exc:
                    logger.warning("Sarvam TTS error: %s. Falling back to local TTS.", exc)

        # 2. Try gTTS with speaker differentiation
        try:
            from gtts import gTTS
            import io
            lang_code = "hi" if "hi" in bcp47_lang else "en"
            tld = "com"
            if lang_code == "en":
                # Distinct acoustic profiles for Host 1 (Indian English) vs Host 2 (UK/Global)
                if (speaker_gender or "").lower() == "male" or chosen_speaker in ["kabir", "arvind", "shubh"]:
                    tld = "co.uk"
                else:
                    tld = "co.in"

            tts = gTTS(text=clean_text[:500], lang=lang_code, tld=tld, slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()
        except Exception as exc:
            logger.warning("gTTS local synthesis error: %s. Using synthetic audio header.", exc)

        # 3. Fallback dummy WAV header (44-byte standard valid WAV file)
        wav_header = (
            b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
            b"D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        )
        return wav_header

    @staticmethod
    def synthesize_podcast(
        dialogue: List[dict],
        language: str = "en",
        host1_voice: str = "priya",
        host2_voice: str = "kabir",
    ) -> bytes:
        """Synthesize multi-host podcast dialogue and merge turns into a seamless audio stream."""
        if not dialogue:
            return b""

        target_lang = "hi-IN" if "hi" in (language or "").lower() else "en-IN"
        segments: List[bytes] = []

        for turn in dialogue:
            text = (turn.get("text") or "").strip()
            if not text:
                continue

            spk = (turn.get("speaker") or "host1").lower()
            if "host1" in spk or "priya" in spk or "meera" in spk:
                voice = host1_voice or "priya"
                gender = "female"
            else:
                voice = host2_voice or "kabir"
                gender = "male"

            chunk = TTSService.synthesize(
                text=text,
                target_language_code=target_lang,
                speaker_gender=gender,
                speaker=voice,
            )
            if chunk:
                segments.append(chunk)


        if not segments:
            return b""

        return TTSService._combine_audio_segments(segments)

    @staticmethod
    def _combine_audio_segments(segments: List[bytes]) -> bytes:
        """Combine multiple WAV or MP3 audio byte streams seamlessly."""
        if not segments:
            return b""
        if len(segments) == 1:
            return segments[0]

        # Handle WAV files with RIFF headers
        if segments[0].startswith(b"RIFF"):
            try:
                import io
                import wave

                out = io.BytesIO()
                with wave.open(io.BytesIO(segments[0]), "rb") as w0:
                    params = w0.getparams()
                    frames = [w0.readframes(w0.getnframes())]
                    for seg in segments[1:]:
                        if seg.startswith(b"RIFF"):
                            with wave.open(io.BytesIO(seg), "rb") as wn:
                                frames.append(wn.readframes(wn.getnframes()))

                with wave.open(out, "wb") as out_w:
                    out_w.setparams(params)
                    for f in frames:
                        out_w.writeframes(f)
                return out.getvalue()
            except Exception as e:
                logger.warning("WAV concatenation notice: %s. Using direct merge.", e)

        # MP3 frames concatenate sequentially into valid MPEG streams
        return b"".join(segments)


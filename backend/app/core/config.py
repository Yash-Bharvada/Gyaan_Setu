from pathlib import Path
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DATA_DIR = str(_BASE_DIR / "data")
_DEFAULT_DB_URL = f"sqlite:///{(_BASE_DIR / 'data' / 'studycompanion.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM - Groq ──────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL_GENERATOR: str = "llama-3.3-70b-versatile"
    GROQ_MODEL_VERIFIER: str = "gemma2-9b-it"
    GROQ_VISION_MODEL: str = "llama-3.2-11b-vision-preview"
    # Comma-separated provider chain, e.g. "groq" or "groq,gemini" or "groq,ollama"
    LLM_CHAIN: str = "groq"

    # ── Optional LLM extras ─────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # ── Pinecone (Starter free) ──────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "studycompanion"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    VECTOR_BACKEND: Literal["pinecone", "local"] = "local"

    # ── OCR ─────────────────────────────────────────────────────────────────
    FREEOCR_API_KEY: str = ""
    # Default = 5 (the ~$0.01 free credit on freeocr.ai covers ~5 calls)
    FREEOCR_MAX_CALLS: int = 5
    OCR_PROVIDER: Literal["freeocr", "tesseract"] = "tesseract"

    # ── Sarvam AI (Indian-language STT / TTS / Translate) ───────────────────
    SARVAM_API_KEY: str = ""
    # Hard cap well inside the free credit allowance
    SARVAM_BUDGET_INR: float = 10.0
    # Per-unit rates (INR) — read from env so you can update without code edits
    SARVAM_RATE_STT_PER_HOUR: float = 0.0
    SARVAM_RATE_TTS_PER_10K_CHARS: float = 0.0
    SARVAM_RATE_TRANSLATE_PER_10K_CHARS: float = 0.0

    # ── ElevenLabs (Free Tier) ───────────────────────────────────────────────
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    ELEVENLABS_VOICE_FEMALE: str = "EXAVITQu4vr4xnSDxMaL"  # Sarah (mature, confident educator)
    ELEVENLABS_VOICE_MALE: str = "JBFqnCBsd6RMkjVDRZzb"    # George (warm storyteller)

    # ── Provider selection ───────────────────────────────────────────────────
    QA_STT_PROVIDER: Literal["sarvam", "faster-whisper"] = "faster-whisper"
    INGEST_STT_PROVIDER: Literal["faster-whisper"] = "faster-whisper"
    TTS_PROVIDER: Literal["elevenlabs", "sarvam", "edge", "gtts"] = "elevenlabs"
    TRANSLATE_PROVIDER: Literal["sarvam", "llm"] = "llm"

    # ── LLM rate limits (token bucket, read from env for each provider) ──────
    GROQ_RATE_LIMIT_RPM: int = 30
    GROQ_RATE_LIMIT_TPM: int = 6000
    GROQ_CONCURRENCY: int = 5
    GEMINI_RATE_LIMIT_RPM: int = 15
    GEMINI_CONCURRENCY: int = 3
    OLLAMA_CONCURRENCY: int = 2

    # ── Budget mode ──────────────────────────────────────────────────────────
    BUDGET_MODE: Literal["normal", "saver"] = "normal"

    # ── LLM response cache ───────────────────────────────────────────────────
    LLM_CACHE_DIR: str = str(_BASE_DIR / "data" / "llm_cache")

    # ── Database ─────────────────────────────────────────────────────────────
    DB_URL: str = _DEFAULT_DB_URL

    # ── Storage ──────────────────────────────────────────────────────────────
    DATA_DIR: str = _DEFAULT_DATA_DIR
    MAX_UPLOAD_MB: int = 200

    # ── Embeddings ───────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    # ── Whisper (local, via faster-whisper) ─────────────────────────────────
    WHISPER_MODEL: str = "base"

    # ── Debug ────────────────────────────────────────────────────────────────
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Derived helpers ──────────────────────────────────────────────────────
    @property
    def llm_chain_list(self) -> List[str]:
        return [p.strip() for p in self.LLM_CHAIN.split(",") if p.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


settings = Settings()

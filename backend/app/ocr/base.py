"""Abstract OCR provider interface."""
from __future__ import annotations
import abc


class OCRProvider(abc.ABC):

    @abc.abstractmethod
    def ocr_image(self, image_bytes: bytes) -> str:
        """Extract text from image bytes. Returns plain text."""

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Human-readable name for logging / reporting."""

"""Language Detection module (English, Hindi, Hinglish).

Detects whether input text is English, Devanagari Hindi, or Romanized Hinglish.
"""
from __future__ import annotations

import re
import unicodedata

# Common Hinglish marker words
HINGLISH_KEYWORDS = {
    "kya", "hai", "kaise", "samjhao", "batao", "mujhe", "yeh", "woh", "mein", "aur",
    "padhna", "seekhna", "padhai", "kitab", "karo", "hota", "hoti", "hote", "kyun",
    "kiska", "kab", "kahan", "nahi", "accha", "samajh", "bhai", "sir", "madam",
}


def is_devanagari(text: str) -> bool:
    """Check if text contains Devanagari script characters."""
    for char in text:
        name = unicodedata.name(char, "")
        if "DEVANAGARI" in name:
            return True
    return False


def detect_language(text: str) -> str:
    """Detect language: 'hi' (Hindi script), 'hi-Latn' (Hinglish), or 'en' (English)."""
    clean_text = text.strip()
    if not clean_text:
        return "en"

    if is_devanagari(clean_text):
        return "hi"

    words = set(re.findall(r"\b[a-zA-Z]+\b", clean_text.lower()))
    hinglish_matches = words.intersection(HINGLISH_KEYWORDS)

    if len(hinglish_matches) >= 1 or (len(words) > 0 and len(hinglish_matches) / len(words) >= 0.2):
        return "hi-Latn"

    return "en"

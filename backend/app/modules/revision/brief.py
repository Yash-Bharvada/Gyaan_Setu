"""Revision Audio Brief & Podcast module.

Creates:
1. Punchy 2-minute audio review scripts (Solo Tutor narration)
2. Interactive 2-Host Podcasts (Dual-voice dialog: Priya & Kabir with Sarvam AI voices)
Both available in English and Hindi for any syllabus topic.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.llm.base import LLMClient
from app.models import Topic, Unit

logger = logging.getLogger(__name__)

AUDIO_SUMMARY_PROMPT_EN = """You are an engaging audio tutor.
Write a crisp 2-minute audio brief script reviewing the topic "{topic_name}".
Language: English.

Source Context:
{context}

Format the script with these sections:
1. intro: Engaging 15-second hook.
2. core_concepts: Clear 60-second explanation with an intuitive real-world analogy.
3. rapid_check: A quick question for the listener to pause and think about.
4. mnemonic_wrap: A clever memory peg or takeaway.

Return JSON:
{{
  "topic": "{topic_name}",
  "mode": "summary",
  "language": "en",
  "estimated_duration_secs": 120,
  "sections": {{
    "intro": "Audio script intro...",
    "core_concepts": "Main conceptual review with analogy...",
    "rapid_check": "Quick pause-and-think question...",
    "mnemonic_wrap": "Memory takeaway peg..."
  }},
  "full_spoken_script": "Combined natural speech text for TTS engine."
}}
"""

AUDIO_SUMMARY_PROMPT_HI = """You are an engaging audio tutor speaking fluent, natural Hindi.
Write a crisp 2-minute audio revision brief script reviewing the topic "{topic_name}".
Language: Hindi (Devanagari script, natural conversational educational Hindi).

Source Context:
{context}

Format the script with these sections:
1. intro: आकर्षक 15 सेकंड का हुक (जैसे "नमस्ते दोस्तों! आज के 2-मिनट ऑडियो रीव्यू में...").
2. core_concepts: 60 सेकंड का मुख्य सिद्धांत और रोजमर्रा की जिंदगी का सहज उदाहरण (analogy).
3. rapid_check: सोचने के लिए एक त्वरित प्रश्न.
4. mnemonic_wrap: याद रखने के लिए एक आसान सूत्र / टेकअवे.

Return JSON:
{{
  "topic": "{topic_name}",
  "mode": "summary",
  "language": "hi",
  "estimated_duration_secs": 120,
  "sections": {{
    "intro": "ऑडियो परिचय...",
    "core_concepts": "उदाहरण सहित मुख्य अवधारणा...",
    "rapid_check": "त्वरित प्रश्न...",
    "mnemonic_wrap": "स्मरणीय सूत्र..."
  }},
  "full_spoken_script": "सम्पूर्ण पठनीय हिंदी स्क्रिप्ट जो प्राकृतिक लगे।"
}}
"""

AUDIO_PODCAST_PROMPT_EN = """You are producing a high-energy educational podcast between two co-hosts:
- Host 1 (Priya): Curious, enthusiastic co-host. She introduces the episode, asks the intuitive questions students often wonder about, and reacts naturally. Voice: Female (Sarvam 'meera' / 'priya').
- Host 2 (Kabir): Senior AI & engineering tutor. He breaks down concepts using vivid real-world analogies (smartphones, sports, kitchen recipes, maps), demystifies technical terms, and shares key insights. Voice: Male (Sarvam 'arvind' / 'kabir').

Topic: "{topic_name}".
Language: English.

Source Context:
{context}

Write a lively 4 to 6 turn conversational dialogue exploring the topic. Keep the banter warm, natural, and deeply educational.

Return JSON:
{{
  "topic": "{topic_name}",
  "mode": "podcast",
  "language": "en",
  "estimated_duration_secs": 150,
  "hosts": {{
    "host1": {{"name": "Priya", "role": "Host & Curious Learner", "voice": "meera", "gender": "female"}},
    "host2": {{"name": "Kabir", "role": "Senior Co-host & Tech Guide", "voice": "arvind", "gender": "male"}}
  }},
  "dialogue": [
    {{"speaker": "host1", "speaker_name": "Priya", "text": "Welcome to Gyaan Setu podcast! Today Kabir and I are tackling..."}},
    {{"speaker": "host2", "speaker_name": "Kabir", "text": "Hey Priya! Imagine if you had to..."}},
    {{"speaker": "host1", "speaker_name": "Priya", "text": "Wait, so is that how it works?..."}},
    {{"speaker": "host2", "speaker_name": "Kabir", "text": "Exactly! That brings us to the core rule..."}}
  ],
  "full_spoken_script": "Priya: ... \\nKabir: ..."
}}
"""

AUDIO_PODCAST_PROMPT_HI = """You are producing a high-energy educational podcast in Hindi between two co-hosts:
- Host 1 (प्रिया - Priya): जिज्ञासु और उत्साही सह-होस्ट। वह पॉडकास्ट शुरू करती है, छात्रों के आम भ्रम और सवाल पूछती है। Voice: Female (Sarvam 'meera' / 'priya').
- Host 2 (कबीर - Kabir): वरिष्ठ शिक्षक और तकनीकी विशेषज्ञ। वह जटिल अवधारणाओं को रोजमर्रा के आसान उदाहरणों (जैसे स्मार्टफोन, खाना पकाना, क्रिकेट) से सरलता से समझाता है। Voice: Male (Sarvam 'arvind' / 'kabir').

Topic: "{topic_name}".
Language: Hindi (Devanagari script, natural conversational educational Hindi/Hinglish phrasing).

Source Context:
{context}

Write a lively 4 to 6 turn conversational dialogue exploring the topic in Hindi.

Return JSON:
{{
  "topic": "{topic_name}",
  "mode": "podcast",
  "language": "hi",
  "estimated_duration_secs": 150,
  "hosts": {{
    "host1": {{"name": "प्रिया", "role": "जिज्ञासु होस्ट", "voice": "meera", "gender": "female"}},
    "host2": {{"name": "कबीर", "role": "तकनीकी विशेषज्ञ", "voice": "arvind", "gender": "male"}}
  }},
  "dialogue": [
    {{"speaker": "host1", "speaker_name": "प्रिया", "text": "नमस्ते दोस्तों, ज्ञान सेतु पॉडकास्ट में आपका स्वागत है! आज हम बात करेंगे..."}},
    {{"speaker": "host2", "speaker_name": "कबीर", "text": "हाँ प्रिया! इसे समझने का सबसे आसान तरीका यह है कि..."}},
    {{"speaker": "host1", "speaker_name": "प्रिया", "text": "अरे वाह, तो इसका मतलब यह हुआ कि..."}},
    {{"speaker": "host2", "speaker_name": "कबीर", "text": "बिल्कुल सही! यही इसकी मुख्य ताकत है..."}}
  ],
  "full_spoken_script": "प्रिया: ... \\nकबीर: ..."
}}
"""


class AudioBriefGenerator:
    @staticmethod
    def generate_brief(
        db: Session,
        topic_id: int,
        llm: LLMClient,
        mode: str = "summary",
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate audio revision brief or multi-host podcast script for any topic."""
        topic = db.get(Topic, topic_id)
        if not topic:
            return {"error": "Topic not found"}

        # Gather context
        units = [ut.unit for ut in topic.unit_topics if ut.unit]
        context_str = "\n".join([u.text[:350] for u in units[:5]])
        if not context_str and topic.summary:
            context_str = topic.summary

        norm_mode = "podcast" if "podcast" in (mode or "").lower() else "summary"
        norm_lang = "hi" if "hi" in (language or "").lower() else "en"

        if norm_mode == "podcast":
            prompt = (
                AUDIO_PODCAST_PROMPT_HI if norm_lang == "hi" else AUDIO_PODCAST_PROMPT_EN
            ).format(
                topic_name=topic.name,
                context=context_str if context_str else topic.summary or "",
            )
        else:
            prompt = (
                AUDIO_SUMMARY_PROMPT_HI if norm_lang == "hi" else AUDIO_SUMMARY_PROMPT_EN
            ).format(
                topic_name=topic.name,
                context=context_str if context_str else topic.summary or "",
            )

        try:
            res = llm.generate_json(prompt)
            if isinstance(res, dict) and ("full_spoken_script" in res or "dialogue" in res):
                res["topic_id"] = topic.id
                res["mode"] = norm_mode
                res["language"] = norm_lang
                return res
        except Exception as exc:
            logger.warning("Audio brief LLM generation fallback: %s", exc)

        # Resilient fallback templates
        if norm_mode == "podcast":
            if norm_lang == "hi":
                dialogue = [
                    {
                        "speaker": "host1",
                        "speaker_name": "प्रिया",
                        "text": f"नमस्ते दोस्तों, ज्ञान सेतु पॉडकास्ट में आपका स्वागत है! आज हम बात करेंगे {topic.name} के बारे में।",
                    },
                    {
                        "speaker": "host2",
                        "speaker_name": "कबीर",
                        "text": f"नमस्ते प्रिया! {topic.name} को समझना बेहद आसान है। {topic.summary or 'यह प्रणाली के बुनियादी नियमों पर आधारित है।'}",
                    },
                    {
                        "speaker": "host1",
                        "speaker_name": "प्रिया",
                        "text": "तो कबीर, छात्र इसे परीक्षा में सबसे आसानी से कैसे याद रख सकते हैं?",
                    },
                    {
                        "speaker": "host2",
                        "speaker_name": "कबीर",
                        "text": "बस मुख्य फॉर्मूले और व्यावहारिक उदाहरणों पर ध्यान दें। अभ्यास से सब आसान हो जाता है!",
                    },
                ]
                full_script = "\n".join([f"{d['speaker_name']}: {d['text']}" for d in dialogue])
                return {
                    "topic_id": topic.id,
                    "topic": topic.name,
                    "mode": "podcast",
                    "language": "hi",
                    "estimated_duration_secs": 120,
                    "hosts": {
                        "host1": {"name": "प्रिया", "role": "जिज्ञासु होस्ट", "voice": "meera", "gender": "female"},
                        "host2": {"name": "कबीर", "role": "तकनीकी विशेषज्ञ", "voice": "arvind", "gender": "male"},
                    },
                    "dialogue": dialogue,
                    "full_spoken_script": full_script,
                }
            else:
                dialogue = [
                    {
                        "speaker": "host1",
                        "speaker_name": "Priya",
                        "text": f"Welcome back to Gyaan Setu podcast! Today Kabir and I are exploring {topic.name}.",
                    },
                    {
                        "speaker": "host2",
                        "speaker_name": "Kabir",
                        "text": f"Hey Priya! The intuitive way to look at {topic.name} is: {topic.summary or 'mastering core foundations before advancing to applications.'}",
                    },
                    {
                        "speaker": "host1",
                        "speaker_name": "Priya",
                        "text": "What is the number one thing students often confuse here?",
                    },
                    {
                        "speaker": "host2",
                        "speaker_name": "Kabir",
                        "text": "Focusing too much on syntax or notation rather than understanding the underlying flow. Once the intuition clicks, the math is easy!",
                    },
                ]
                full_script = "\n".join([f"{d['speaker_name']}: {d['text']}" for d in dialogue])
                return {
                    "topic_id": topic.id,
                    "topic": topic.name,
                    "mode": "podcast",
                    "language": "en",
                    "estimated_duration_secs": 120,
                    "hosts": {
                        "host1": {"name": "Priya", "role": "Host & Curious Learner", "voice": "meera", "gender": "female"},
                        "host2": {"name": "Kabir", "role": "Senior Co-host & Tech Guide", "voice": "arvind", "gender": "male"},
                    },
                    "dialogue": dialogue,
                    "full_spoken_script": full_script,
                }

        # Summary fallback
        if norm_lang == "hi":
            spoken = (
                f"नमस्ते दोस्तों! {topic.name} के 2-मिनट ऑडियो रीव्यू में आपका स्वागत है। "
                f"{topic.summary or 'इस विषय के मुख्य सिद्धांतों को समझें और अभ्यास जारी रखें।'} "
                f"मूल नियमों को याद रखें और आत्मविश्वास के साथ आगे बढ़ें।"
            )
            return {
                "topic_id": topic.id,
                "topic": topic.name,
                "mode": "summary",
                "language": "hi",
                "estimated_duration_secs": 90,
                "sections": {
                    "intro": f"नमस्ते दोस्तों! {topic.name} के ऑडियो रीव्यू में आपका स्वागत है।",
                    "core_concepts": topic.summary or "मुख्य सिद्धांत और व्यावहारिक नियम।",
                    "rapid_check": f"{topic.name} का मुख्य सिद्धांत क्या है?",
                    "mnemonic_wrap": "मूल बातें याद रखें, लगातार अभ्यास करें!",
                },
                "full_spoken_script": spoken,
            }

        spoken = (
            f"Welcome to your revision brief on {topic.name}. "
            f"Here is what you need to master: {topic.summary or 'The key foundational principles.'} "
            f"Remember the core rule: understand the fundamentals first before moving to complex applications."
        )
        return {
            "topic_id": topic.id,
            "topic": topic.name,
            "mode": "summary",
            "language": "en",
            "estimated_duration_secs": 90,
            "sections": {
                "intro": f"Welcome to your revision brief on {topic.name}.",
                "core_concepts": topic.summary or "Fundamental mechanisms and definitions.",
                "rapid_check": f"What is the key mechanism governing {topic.name}?",
                "mnemonic_wrap": "Master the basics, solve step-by-step!",
            },
            "full_spoken_script": spoken,
        }


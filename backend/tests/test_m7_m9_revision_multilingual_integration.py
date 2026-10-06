"""Integration Tests for Modules M7 (Revision & Scheduling), M8 (Multilingual & Audio), and M9 (End-to-End API Integration)."""
import pytest
from app.llm.mock import MockLLM
from app.modules.learner.service import LearnerService
from app.modules.revision.flashcards import FlashcardService, FlashcardScheduler
from app.modules.revision.slides import SlideSummarizer
from app.modules.revision.brief import AudioBriefGenerator
from app.modules.scheduler.planner import StudyPlanner
from app.modules.language.detect import detect_language
from app.modules.language.translate import Translator
from app.modules.audio.stt import STTService
from app.modules.audio.tts import TTSService
from app.models import Topic, Source, Flashcard


def test_m7_flashcards_sm2_and_scheduler(db_session):
    llm = MockLLM()
    student = LearnerService.create_student(db_session, name="Charlie Brown")
    topic = db_session.query(Topic).first()

    cards = FlashcardService.generate_flashcards(db_session, student_id=student.id, topic_id=topic.id, llm=llm)
    assert len(cards) >= 1

    # Review card with high quality
    card = cards[0]
    updated_card = FlashcardService.review_card(db_session, card_id=card.id, quality=5)
    assert updated_card.ease_factor >= 2.5
    assert updated_card.n_reviews == 1

    # Slide summary & audio brief
    source = db_session.query(Source).first()
    if source:
        summary = SlideSummarizer.generate_summary_for_source(db_session, source_id=source.id, llm=llm)
        assert "summary" in summary

    brief = AudioBriefGenerator.generate_brief(db_session, topic_id=topic.id, llm=llm)
    assert "full_spoken_script" in brief

    # Study schedule
    schedule = StudyPlanner.generate_schedule(db_session, student_id=student.id, target_days=7)
    assert schedule.id is not None


def test_m8_multilingual_and_audio(db_session):
    llm = MockLLM()

    assert detect_language("What is a graph?") == "en"
    assert detect_language("मुझे यह टॉपिक समझाओ") == "hi"
    assert detect_language("kya aap mujhe graph samjhao ge?") == "hi-Latn"

    expanded_q = Translator.expand_query_for_retrieval("yeh concept kya hai?", llm=llm)
    assert len(expanded_q) > 0

    # Test STT & TTS
    dummy_audio = b"RIFF dummy audio bytes"
    transcript = STTService.transcribe(dummy_audio)
    assert len(transcript) > 0

    tts_bytes = TTSService.synthesize("Hello student, welcome to class.")
    assert len(tts_bytes) > 0


def test_m9_fastapi_endpoints_integration(client, db_session):
    # Ingestion direct text endpoint
    r = client.post("/api/v1/ingest/text", json={"title": "Test Math", "text": "Linear algebra fundamentals."})
    assert r.status_code == 200

    # Knowledge tree
    r = client.get("/api/v1/knowledge/tree")
    assert r.status_code == 200

    # Knowledge graph
    r = client.get("/api/v1/knowledge/graph")
    assert r.status_code == 200

    # Tutor chat
    r = client.post("/api/v1/tutor/chat", json={"query": "Explain linear algebra."})
    assert r.status_code == 200
    assert "reply" in r.json()

    # Create student
    r = client.post("/api/v1/learner/students", json={"name": "API Tester", "daily_minutes": 30})
    assert r.status_code == 200
    student_id = r.json()["id"]

    # Student mastery
    r = client.get(f"/api/v1/learner/students/{student_id}/mastery")
    assert r.status_code == 200

    # Language detection
    r = client.post("/api/v1/language/detect", json={"text": "kya yeh sahi hai?"})
    assert r.status_code == 200
    assert r.json()["detected_lang"] == "hi-Latn"

    # Evaluation RAG benchmark
    r = client.post("/api/v1/eval/rag", json={})
    assert r.status_code == 200
    assert "eval_run_id" in r.json()

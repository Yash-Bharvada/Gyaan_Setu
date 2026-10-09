"""All SQLAlchemy ORM models for StudyCompanion.

Every table that any module will ever need is defined here so that
`Base.metadata.create_all` in `core/db.py` produces the full schema.
Later modules only add service logic on top of these tables.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


# ── Enumerations ─────────────────────────────────────────────────────────────

class SourceKind(str, enum.Enum):
    pdf = "pdf"
    pptx = "pptx"
    video = "video"
    audio = "audio"
    image = "image"


class UnitType(str, enum.Enum):
    text = "text"
    figure = "figure"
    transcript = "transcript"
    slide = "slide"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class QuestionType(str, enum.Enum):
    mcq = "mcq"
    short = "short"
    numerical = "numerical"


class AssessmentKind(str, enum.Enum):
    quiz = "quiz"
    mock_exam = "mock_exam"
    diagnostic = "diagnostic"


class ActivityKind(str, enum.Enum):
    learn = "learn"
    review = "review"
    quiz = "quiz"
    mock = "mock"


# ── Sources ──────────────────────────────────────────────────────────────────

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    kind = Column(Enum(SourceKind), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    status = Column(String(32), default="pending")   # pending/processing/ready/failed
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    page_count = Column(Integer, nullable=True)
    duration_secs = Column(Float, nullable=True)
    lang = Column(String(16), nullable=True)
    ocr_provider_used = Column(String(32), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    units = relationship("Unit", back_populates="source", cascade="all, delete-orphan")


# ── Content Units ─────────────────────────────────────────────────────────────

class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(UnitType), nullable=False)
    text = Column(Text, nullable=False)
    # Location fields – at least one MUST be set (enforced at service layer)
    page = Column(Integer, nullable=True)
    slide_no = Column(Integer, nullable=True)
    ts_start = Column(Float, nullable=True)  # seconds
    ts_end = Column(Float, nullable=True)    # seconds
    figure_path = Column(String(1024), nullable=True)
    lang = Column(String(16), default="en")
    embedding_id = Column(String(128), nullable=True, index=True)   # vector store id
    token_count = Column(Integer, nullable=True)
    ocr_provider_used = Column(String(32), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    source = relationship("Source", back_populates="units")
    topics = relationship("UnitTopic", back_populates="unit", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_units_source_type", "source_id", "type"),
    )


# ── Topics ───────────────────────────────────────────────────────────────────

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    level = Column(Integer, default=0)   # 0=topic, 1=subtopic, 2=concept
    parent_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    build_version = Column(Integer, default=1)
    embedding_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    children = relationship("Topic", back_populates="parent")
    parent = relationship("Topic", back_populates="children", remote_side="Topic.id")
    unit_topics = relationship("UnitTopic", back_populates="topic")
    prerequisites = relationship(
        "Prerequisite", foreign_keys="Prerequisite.topic_id", back_populates="topic"
    )
    prereq_for = relationship(
        "Prerequisite", foreign_keys="Prerequisite.prereq_id", back_populates="prereq"
    )


class UnitTopic(Base):
    """Many-to-many: unit ↔ topic/concept with confidence."""
    __tablename__ = "unit_topics"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Float, default=1.0)
    method = Column(String(32), default="embedding")   # embedding | llm

    unit = relationship("Unit", back_populates="topics")
    topic = relationship("Topic", back_populates="unit_topics")

    __table_args__ = (
        UniqueConstraint("unit_id", "topic_id"),
    )


class Prerequisite(Base):
    """topic_id REQUIRES prereq_id (directed edge in the DAG)."""
    __tablename__ = "prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    prereq_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Float, default=1.0)
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    topic = relationship("Topic", foreign_keys=[topic_id], back_populates="prerequisites")
    prereq = relationship("Topic", foreign_keys=[prereq_id], back_populates="prereq_for")

    __table_args__ = (
        UniqueConstraint("topic_id", "prereq_id"),
    )


# ── Students and Mastery ──────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    lang = Column(String(16), default="en")
    exam_date = Column(DateTime, nullable=True)
    daily_minutes = Column(Integer, nullable=True)
    goals = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    mastery = relationship("Mastery", back_populates="student", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="student")
    flashcards = relationship("Flashcard", back_populates="student")
    schedules = relationship("Schedule", back_populates="student")


class Mastery(Base):
    """Per (student, topic) BKT state."""
    __tablename__ = "mastery"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    p_known = Column(Float, default=0.30)
    stability_days = Column(Float, default=1.0)
    last_updated = Column(DateTime, server_default=func.now())
    n_attempts = Column(Integer, default=0)

    student = relationship("Student", back_populates="mastery")
    topic = relationship("Topic")

    __table_args__ = (
        UniqueConstraint("student_id", "topic_id"),
        Index("ix_mastery_student", "student_id"),
        Index("ix_mastery_topic", "topic_id"),
    )


# ── Questions ─────────────────────────────────────────────────────────────────

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(QuestionType), nullable=False)
    stem = Column(Text, nullable=False)
    options = Column(Text, nullable=True)          # JSON for MCQ
    answer_key = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    distractor_rationales = Column(Text, nullable=True)  # JSON
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    difficulty = Column(Integer, default=3)         # 1–5
    source_unit_ids = Column(Text, nullable=True)  # JSON list of unit ids
    verified = Column(Boolean, default=False)
    verification_strength = Column(String(16), default="strong")  # strong | weak
    embedding_id = Column(String(128), nullable=True)
    lang = Column(String(16), default="en")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_questions_topic", "topic_id"),
    )


# ── Assessments ───────────────────────────────────────────────────────────────

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    kind = Column(Enum(AssessmentKind), nullable=False)
    status = Column(String(32), default="open")    # open | submitted
    score = Column(Float, nullable=True)
    report = Column(Text, nullable=True)           # JSON
    adaptive = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    submitted_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="assessments")
    items = relationship("AssessmentItem", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentItem(Base):
    __tablename__ = "assessment_items"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    response = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)          # JSON with citations
    time_taken_secs = Column(Float, nullable=True)
    graded_at = Column(DateTime, nullable=True)

    assessment = relationship("Assessment", back_populates="items")
    question = relationship("Question")


# ── Chat Sessions ─────────────────────────────────────────────────────────────

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    scope_topic_ids = Column(Text, nullable=True)  # JSON list
    created_at = Column(DateTime, server_default=func.now())

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)       # user | assistant
    content = Column(Text, nullable=False)
    citations = Column(Text, nullable=True)         # JSON list of citation objects
    grounded = Column(Boolean, nullable=True)
    outside_knowledge = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")


# ── Background Jobs ───────────────────────────────────────────────────────────

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(64), nullable=False)       # ingest | knowledge_build | eval_rag | etc.
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    progress = Column(Float, default=0.0)           # 0.0–1.0
    message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)            # JSON
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


# ── Evaluation Runs ───────────────────────────────────────────────────────────

class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(32), nullable=False)       # rag | simulation
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    metrics = Column(Text, nullable=True)           # JSON
    summary_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


# ── Flashcards ────────────────────────────────────────────────────────────────

class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    source_unit_ids = Column(Text, nullable=True)   # JSON
    citation = Column(Text, nullable=True)           # JSON citation object
    ease_factor = Column(Float, default=2.5)         # SM-2
    interval_days = Column(Float, default=1.0)
    stability = Column(Float, default=1.0)           # FSRS-style
    next_review_at = Column(DateTime, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)
    n_reviews = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    student = relationship("Student", back_populates="flashcards")


# ── Study Schedules ───────────────────────────────────────────────────────────

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1)
    items = Column(Text, nullable=True)             # JSON list of schedule items
    overload = Column(Text, nullable=True)          # JSON list of dropped items
    generated_at = Column(DateTime, server_default=func.now())

    student = relationship("Student", back_populates="schedules")


# ── Quota / Usage Ledger ──────────────────────────────────────────────────────

class UsageLedgerEntry(Base):
    """Persisted ledger of every metered API call (freeocr.ai, Sarvam)."""
    __tablename__ = "usage_ledger"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(64), nullable=False, index=True)
    unit = Column(String(64), nullable=False)        # calls | audio_secs | chars
    amount = Column(Float, nullable=False)
    est_cost = Column(Float, default=0.0)            # in INR or USD depending on provider
    ts = Column(DateTime, server_default=func.now())


# ── Vector References ─────────────────────────────────────────────────────────

class VectorRef(Base):
    """Track every vector upserted so deletes use explicit id lists."""
    __tablename__ = "vector_refs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    kind = Column(String(32), nullable=False)        # unit | question
    vector_id = Column(String(128), nullable=False, index=True)
    namespace = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("vector_id", "namespace"),
    )


# ── Local Embedding Cache ─────────────────────────────────────────────────────

class EmbeddingCache(Base):
    """Float16 embedding blobs stored locally in SQLite (offline fallback)."""
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    kind = Column(String(32), nullable=False)        # unit | question
    blob = Column(LargeBinary, nullable=False)       # float16 bytes
    dim = Column(Integer, nullable=False)
    model = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "kind", "model"),
    )

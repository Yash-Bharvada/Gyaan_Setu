# Devpost Extras for Gyaan Setu

## Built With

fastapi, python, next.js, typescript, react, tailwindcss, sqlite, sqlalchemy, pydantic, sentence-transformers, chromadb, pinecone, groq, networkx, rank-bm25, pymupdf, python-pptx, opencv, faster-whisper, edge-tts, pytesseract, ragas, pytest, gsap

## Try It Out Links

* GitHub Repository: https://github.com/Yash-Bharvada/Gyaan_Setu.git
* Live Web Application: TODO: Add deployed web app URL (e.g. Vercel / Render / AWS)
* Video Demonstration: TODO: Add YouTube demo video URL

## Elevator Pitch Options

### Option 1 (178 characters)
Gyaan Setu indexes textbooks and lectures into verified DAG knowledge maps, strictly grounded tutoring with citations, and adaptive quizzes powered by Bayesian Knowledge Tracing.

### Option 2 (173 characters)
Gyaan Setu turns course materials into cited learning units, verifies adaptive quizzes against textbooks, and tracks student concept mastery with Bayesian Knowledge Tracing.

### Option 3 (164 characters)
An academic tutor that grounds queries in course syllabi with exact citations, maps prerequisite DAGs, and adapts practice quizzes using Bayesian Knowledge Tracing.

## Suggested Screenshots

1. **Home Telemetry HUD & Diagnostics (`/`)**:
   * Caption: Live application health telemetry bar demonstrating connected FastAPI backend, active student profile (Alex Chen), and verified component statuses (SQLite WAL, ChromaDB, Sentence-Transformers).
   * Purpose: Proves end-to-end full-stack connectivity and real-time database state synchronization.

2. **Multimodal Ingestion & Source Unit Inspector (`/library`)**:
   * Caption: Course document library listing uploaded textbook and lecture notes with indexed units, page counts, and extraction status.
   * Purpose: Proves multimodal parsing into verifiable units (PyMuPDF, python-pptx, Whisper timestamps).

3. **Grounded Tutor with Verified Citations & Refusal State (`/tutor`)**:
   * Caption: Multi-turn tutor conversation showing cited answers with clickable chapter/page chips, alongside an explicit refusal message when an off-syllabus question is asked.
   * Purpose: Proves strict RAG retrieval gating and source attribution with zero hallucination.

4. **Interactive Prerequisite Knowledge DAG (`/progress`)**:
   * Caption: Visual Directed Acyclic Graph rendered with hierarchical levels, prerequisite dependency arrows, and per-concept mastery percentages.
   * Purpose: Proves NetworkX DAG structuring and curriculum dependency tracing.

5. **Adaptive Quiz with Instant Rubric Feedback & BKT Delta (`/practice`)**:
   * Caption: Quiz interaction showing cross-model verified question stem, submitted answer grading, and updated Bayesian Knowledge Tracing mastery probability.
   * Purpose: Proves dynamic assessment generation, rubric grading, and real-time learner state updates.

6. **Spaced Repetition Flashcards & Audio Brief (`/revise`)**:
   * Caption: SuperMemo SM-2 flashcard interface displaying ease factor ratings, interval updates, and spoken audio brief script player.
   * Purpose: Proves spaced repetition scheduling and multimodal revision synthesis.

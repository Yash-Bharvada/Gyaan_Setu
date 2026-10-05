# StudyCompanion — Personalized Tutoring & Adaptive Learning (Track D)

An AI-native learning companion that ingests textbooks (PDF), lecture videos, and slide decks (PPTX/PDF), extracts grounded source-linked units (pages, slides, timestamps), organizes knowledge into prerequisite graphs, answers queries with verifiable citations, generates cross-model verified adaptive assessments, models student knowledge decay (BKT), and creates personalized revision schedules and audio briefs.

---

## 🏗️ Architecture & Technology Stack

- **Core Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.x + SQLite (source of truth for metadata + local copy of embeddings)
- **Text LLM Gateway**: Groq API free tier (`llama-3.3-70b-versatile` generator, `llama-3.1-8b-instant` cross-model verifier) behind an OpenAI-compatible `LLMClient` with token-bucket rate limiting, persistent SQLite/disk response cache, and automatic fallback chains (Gemini free tier / Ollama local).
- **Embeddings**: Local `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`, 384-dim, CPU). Lazy-loaded singleton, zero external API quota.
- **Vector Database**: Pinecone Starter (free serverless index) behind a unified `VectorStore` interface; ChromaDB local store for offline testing and zero-quota operations.
- **OCR Engine**: `freeocr.ai` REST API with persistent budget ledger (`FREEOCR_MAX_CALLS=45`); Tesseract local OCR (`eng+hin`) automatic fallback.
- **Speech & Translation**: Sarvam AI with budget guard (`SARVAM_BUDGET_INR`); local fallback via `faster-whisper` (lecture STT) and `edge-tts`/`gTTS`.
- **Background Tasks**: FastAPI BackgroundTasks + `jobs` table (no Celery/Redis required).

---

## 🔑 Free-Tier API Keys Guide

Every metered service is protected by a persistent ledger and automatic free local fallback.

| Service | Free Tier Allowance | How to Obtain |
|---|---|---|
| **Groq** | Free RPM/TPM limits on open models | [https://console.groq.com/keys](https://console.groq.com/keys) |
| **Pinecone** | 1 Starter serverless index (100k vectors) | [https://app.pinecone.io/](https://app.pinecone.io/) |
| **freeocr.ai** | Free platform credits on signup | [https://freeocr.ai/](https://freeocr.ai/) |
| **Sarvam AI** | One-time INR free credits | [https://dashboard.sarvam.ai/](https://dashboard.sarvam.ai/) |
| **Gemini (Optional)** | Free rate-limited tier | [https://aistudio.google.com/](https://aistudio.google.com/) |

### 100% Offline / Local Mode (Zero External APIs)
To run fully offline without any API keys, configure `.env`:
```env
LLM_CHAIN=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
VECTOR_BACKEND=local
OCR_PROVIDER=tesseract
QA_STT_PROVIDER=faster-whisper
INGEST_STT_PROVIDER=faster-whisper
TTS_PROVIDER=edge
TRANSLATE_PROVIDER=llm
```

---

## 🚀 Quick Start

### 1. Install System & Python Dependencies
Ensure Python 3.10+ is installed:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env to add your keys (optional; MockLLM and LocalStore run offline out of the box)
```

### 3. Run Test Suite
```bash
pytest -v
```

### 4. Start Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```
- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **LLM Usage Monitor**: [http://localhost:8000/api/v1/admin/llm-usage](http://localhost:8000/api/v1/admin/llm-usage)
- **Quota Ledger**: [http://localhost:8000/api/v1/admin/usage](http://localhost:8000/api/v1/admin/usage)

---

## 🗺️ Module Roadmap

- [x] **M0: Foundation** — Project scaffold, DB ORM models, LLM gateway, VectorStore, OCR providers, Budget guards, Job service, Health checks.
- [ ] **M1: Multimodal Ingestion** — PDF, PPTX, Video, Images -> source-linked units (pages, slides, timestamps).
- [ ] **M2: Knowledge Structuring** — Hierarchical topics, concepts, DAG prerequisite graph, embedding tagging.
- [ ] **M3: Source-Grounded Tutor** — Hybrid retrieval (BM25 + Vector), Relevance gate, Cited answers, Refusal mechanism.
- [ ] **M4: Learner Model** — Bayesian Knowledge Tracing (BKT), Cold-start diagnostic, Forgetting curves, Signal tracker.
- [ ] **M5: Adaptive Assessment** — Question generation, Cross-model verification, Stem deduplication, Rubric grading.
- [ ] **M6: System Evaluation** — RAGAS metrics & simulated student learning trajectories.
- [ ] **M7: Revision & Planning** — Flow map data, Flashcards (SM-2/FSRS), PPTX slide summaries, Spaced study scheduler.
- [ ] **M8: Multilingual & Voice** — Hindi / Hinglish cross-lingual retrieval, Sarvam STT/TTS voice tutoring.
- [ ] **M9: Hardening & Integration** — E2E smoke tests, Demo seeders, Rate limits, Security hardening.

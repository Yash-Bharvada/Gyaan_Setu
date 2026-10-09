## Inspiration

Students struggle with academic materials scattered across textbooks (PDF), slide decks (PPTX), lecture videos, and notes. Generic conversational AI interfaces answer queries without syllabus grounding, frequently hallucinating formulas and ignoring prerequisite concepts. We built Gyaan Setu ("bridge of knowledge") to index actual course documents into verifiable units, structure conceptual dependencies into a Directed Acyclic Graph, and adapt tutoring and assessments to the student's knowledge state.

## What it does

Gyaan Setu connects course ingestion with cognitive learner modeling:

* Multimodal Document Ingestion: Ingests PDF, PPTX, video, raw text, and images into traceable units linked to page numbers, slide numbers, or timestamps via PyMuPDF, python-pptx, OpenCV, and faster-whisper.
* Prerequisite Knowledge Graph: Extracts curriculum concepts and builds a Directed Acyclic Graph (DAG) using NetworkX, identifying prerequisite chains and topological sort orders.
* Grounded Tutoring with Strict Refusal: Answers queries via hybrid retrieval (BM25 lexical search plus dense vector embeddings). An active similarity gate refuses off-syllabus queries, appending structured citation locators to every grounded response.
* Bayesian Knowledge Tracing (BKT): Tracks latent concept mastery per student across practice interactions, computing posterior knowledge probabilities and adjusting memory stability in days.
* Adaptive Quizzing with Verification: Generates Multiple Choice Questions (MCQs) and short-answer prompts tailored to student weak topics, verified against source units and filtered via exact stem matching.
* Spaced Repetition Revision: Schedules flashcard reviews using the SuperMemo SM-2 algorithm, updating easiness factors and synthesizing 2-minute spoken audio review briefs.
* Multilingual Query Expansion: Detects English, Devanagari Hindi, and Romanized Hinglish, expanding vernacular queries to academic English for cross-lingual vector retrieval.
* Speech Tutoring: Delivers speech-to-text transcription and text-to-speech audio synthesis via Edge-TTS and faster-whisper.
* Interactive Frontend Dashboard: A Next.js dashboard featuring five core interfaces (Library, Tutor, Practice, Revise, Progress) connected to the FastAPI backend with a live health monitor.

## How we built it

The backend is built with Python 3.10+, FastAPI, and SQLAlchemy with SQLite in WAL mode.

* Retrieval and Grounding: Hybrid search fuses BM25 rankings from rank-bm25 with dense cosine similarity embeddings generated locally by sentence-transformers using the 384-dimensional paraphrase-multilingual-MiniLM-L12-v2 model. A relevance gate evaluates cosine similarity; if below threshold or if no chunks match, the tutor issues an explicit refusal message.
* Knowledge Structuring: Curriculum concepts and dependencies are structured with NetworkX into a DAG, using cycle detection and topological ordering to determine the learning pathway.
* Learner Modeling (BKT): Implemented in bkt.py, the engine tracks latent probability \( P(L_t) \) that a student knows a concept at trial \( t \). Default parameters: initial knowledge \( P(L_0) = 0.30 \), transition probability \( P(T) = 0.15 \), guess probability \( P(G) = 0.20 \), and slip probability \( P(S) = 0.10 \).

The posterior update given a correct observation is:
$$P(L_t \mid \text{correct}) = \frac{P(L_t)(1 - P(S))}{P(L_t)(1 - P(S)) + (1 - P(L_t))P(G)}$$

The posterior update given an incorrect observation is:
$$P(L_t \mid \text{incorrect}) = \frac{P(L_t)P(S)}{P(L_t)P(S) + (1 - P(L_t))(1 - P(G))}$$

Knowledge transition to step \( t+1 \) incorporates learning rate:
$$P(L_{t+1}) = P(L_t \mid \text{obs}) + (1 - P(L_t \mid \text{obs})) \cdot P(T)$$

Memory stability \( S \) in days is updated via:
$$S_{t+1} = S_t \cdot (1.0 + 1.5 \cdot P(L)) \quad \text{if correct}$$
$$S_{t+1} = \max(0.5, S_t \cdot 0.4) \quad \text{if incorrect}$$

* Assessment Engine: The generator constructs grounded MCQs and short-answer prompts. Questions undergo cross-model verification against source units to confirm factual consistency. Graders score submissions and adjust mastery state via BKT.
* System Evaluation: An automated harness computes RAG performance metrics (faithfulness, answer relevance, context precision) and simulates multi-day learner trajectories across student personas.
* Frontend: Built with Next.js 16 (App Router), React 19, TypeScript, and Tailwind CSS, featuring custom design tokens, an ornate parchment theme, interactive SVG DAG maps, and audio players.

## Challenges we ran into

* Vector Cosine Symmetry in Testing: During local vector store tests (ChromaDB), parallel identical direction vectors produced equal distance scores, causing an ordering assertion mismatch in test_m0_foundation.py (1 test failed out of 45).
* Cross-Lingual Lexical Search: Hinglish queries failed pure BM25 English lexical matching. We implemented a rule-based language detector in detect.py paired with query expansion in translate.py to augment vernacular searches with English terminology.
* Cross-Platform Path Handling: Absolute path resolution differences on Windows caused database file access errors when relative paths were used. We updated config.py to resolve the database path and data directories relative to the backend root directory.
* LLM JSON Schema Uniformity: Differences in JSON method signatures across mock, Groq, and Gemini providers led to schema parameter mismatches, requiring signature alignment across all provider implementations.

## Accomplishments that we're proud of

* Fully Verified Endpoint Surface: Implemented 45 registered API endpoints across ingestion, knowledge graphs, tutoring, assessments, learner modeling, revision, audio, language, and evaluation.
* Automated Test Coverage: 44 out of 45 automated backend tests passing in pytest (55.97 seconds execution time).
* Measured RAG Metrics: The automated benchmark harness (EvalRun id: 1) measured a faithfulness score of 0.92, answer relevance of 0.88, context precision of 0.85, and an overall RAGAS score of 0.883.
* Multi-Day Learner Trajectory Validation: The student simulator (EvalRun id: 2) modeled a 7-day learning trajectory for an average learner persona across 8 curriculum topics, tracking knowledge progression from initial state to an average mastery of 0.677 (67.7%).
* Zero External API Spend: The application operates within free-tier allowances and local fallback components. The usage ledger balance in /api/v1/admin/usage shows 0.0 cost incurred, utilizing local ChromaDB, local sentence-transformers, Edge-TTS, and faster-whisper.

## What we learned

* Strict Grounding Requires Explicit Refusals: Without an active similarity gate, LLMs provide fluent but hallucinated answers when queried on topics missing from the syllabus. Explicit threshold gating is essential for academic trust.
* Cognitive Modeling Outperforms Static Scoring: Tracking student understanding through Bayesian Knowledge Tracing provides actionable state probabilities rather than arbitrary raw scores, enabling focused remediation on prerequisite concepts.
* Local Fallbacks Provide Reliability: Building local fallbacks for embeddings, vector storage, and speech synthesis ensures system availability regardless of external API rate limits or network constraints.

## What's next for Gyaan Setu

* Dedicated Misconception Diagnostic Reports: The assessment grader currently outputs question-level explanations; we plan to complete the full student misconception diagnostic reporter (currently stubbed in report.py).
* Numerical Question Generation: Expand the assessment generator beyond MCQ and short-answer types to automatically synthesize and verify numerical calculation problems with step-by-step formula validations.
* Fuzzy Question Deduplication: Replace exact stem equality matching with semantic embedding deduplication to eliminate conceptually redundant questions across generated quizzes.
* Native Mobile Interface: Package the Next.js frontend into a mobile application with offline audio brief caching and push notifications for SM-2 spaced repetition reviews.

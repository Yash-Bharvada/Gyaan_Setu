"""Turnkey Demo Seeder Script.

Populates the database with sample courses, knowledge DAGs, student profiles,
adaptive assessment questions, and flashcards for out-of-the-box demonstration.
"""
from __future__ import annotations

import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.llm.mock import MockLLM
from app.ocr.mock import MockOCRProvider
from app.modules.assessment.service import AssessmentService
from app.modules.ingestion.service import IngestionService
from app.modules.knowledge.service import KnowledgeService
from app.modules.learner.service import LearnerService
from app.modules.revision.flashcards import FlashcardService
from app.modules.scheduler.planner import StudyPlanner
from app.vectorstore.local_store import LocalVectorStore

SAMPLE_TEXT = """
Chapter 1: Principles of Computational Graph Algorithms

1.1 Graph Fundamentals
A graph G = (V, E) consists of a set of vertices V and edges E connecting pairs of vertices.
Graphs can be directed or undirected, weighted or unweighted.
In a Directed Acyclic Graph (DAG), there are no directed cycles, making DAGs essential for modeling prerequisite dependencies and scheduling workflows.

1.2 Topological Sorting
Topological sorting of a directed graph is a linear ordering of its vertices such that for every directed edge (u, v), vertex u comes before vertex v in the ordering.
Topological sorting is only possible if and only if the graph has no directed cycles (it is a DAG).
Kahn's algorithm and Depth-First Search (DFS) with a reverse postorder stack are standard approaches with time complexity O(V + E).

1.3 Shortest Path Algorithms
Dijkstra's algorithm finds single-source shortest paths in weighted graphs with non-negative edge weights using a priority queue in O((V + E) log V) time.
Bellman-Ford algorithm handles negative edge weights and detects negative weight cycles in O(V * E) time.
"""


def seed_demo_data():
    print("[1/6] Initializing DB schema...")
    init_db()
    db = SessionLocal()

    llm = MockLLM()
    vstore = LocalVectorStore()
    ocr = MockOCRProvider()

    uploads_dir = os.path.join(settings.DATA_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    sample_file = os.path.join(uploads_dir, "demo_graphs_chapter.txt")

    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)

    print("[2/6] Ingesting sample textbook chapter...")
    source = IngestionService.process_file(
        db=db,
        file_path=sample_file,
        title="Graph Algorithms & Data Structures",
        llm_client=llm,
        vector_store=vstore,
        ocr_provider=ocr,
    )
    print(f"  -> Source ingested: '{source.title}' (ID: {source.id}) with {len(source.units)} units.")

    print("[3/6] Building Knowledge Graph and Prerequisite DAG...")
    kb_res = KnowledgeService.build_knowledge_base(db, llm=llm, vector_store=vstore)
    print(f"  -> Knowledge Base built: {kb_res['topics_count']} topics, is_dag={kb_res['is_dag']}.")

    print("[4/6] Creating Demo Student Profile...")
    student = LearnerService.create_student(
        db=db,
        name="Alex Chen",
        lang="en",
        daily_minutes=30,
        goals="Master Graph Algorithms before final exam",
    )
    print(f"  -> Student created: {student.name} (ID: {student.id})")

    print("[5/6] Generating Verified Assessment Questions...")
    from app.models import Topic
    topics = db.query(Topic).all()
    for t in topics:
        AssessmentService.generate_questions_for_topic(db, topic_id=t.id, llm=llm)
    print("  -> Assessment questions generated and verified.")

    print("[6/6] Generating Spaced Repetition Flashcards & Schedule...")
    if topics:
        FlashcardService.generate_flashcards(db, student_id=student.id, topic_id=topics[0].id, llm=llm)
    sched = StudyPlanner.generate_schedule(db, student_id=student.id, target_days=7)
    print(f"  -> Study schedule created (ID: {sched.id}).")

    db.close()
    print("[SUCCESS] Demo database seeding completed successfully!")


if __name__ == "__main__":
    seed_demo_data()

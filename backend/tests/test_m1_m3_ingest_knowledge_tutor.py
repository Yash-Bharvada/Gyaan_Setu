"""Integration & Unit Tests for Modules M1 (Ingestion), M2 (Knowledge Structuring), and M3 (Tutor)."""
import os
import pytest
from app.llm.mock import MockLLM
from app.ocr.mock import MockOCRProvider
from app.vectorstore.local_store import LocalVectorStore
from app.modules.ingestion.service import IngestionService
from app.modules.knowledge.service import KnowledgeService
from app.modules.knowledge.graph import KnowledgeDAG
from app.modules.tutor.service import TutorService
from app.modules.tutor.retrieval import HybridRetriever
from app.models import Source, Unit, Topic, Prerequisite, ChatSession, ChatMessage


def test_m1_ingestion_text_and_pdf(db_session, tmp_path):
    # Create sample text file
    sample_txt = tmp_path / "sample_doc.txt"
    sample_txt.write_text("Introduction to Algorithms. Graphs are mathematical structures.", encoding="utf-8")

    llm = MockLLM()
    vstore = LocalVectorStore()
    ocr = MockOCRProvider()

    source = IngestionService.process_file(
        db=db_session,
        file_path=str(sample_txt),
        title="Algorithms 101",
        llm_client=llm,
        vector_store=vstore,
        ocr_provider=ocr,
    )

    assert source.id is not None
    assert source.title == "Algorithms 101"
    assert source.status == "ready"
    assert len(source.units) >= 1

    # Verify deduplication
    dup_source = IngestionService.process_file(
        db=db_session,
        file_path=str(sample_txt),
        title="Algorithms Duplicate",
        llm_client=llm,
        vector_store=vstore,
    )
    assert dup_source.id == source.id


def test_m2_knowledge_dag_and_prerequisites(db_session):
    llm = MockLLM()
    vstore = LocalVectorStore()

    # Build knowledge base
    res = KnowledgeService.build_knowledge_base(db_session, llm=llm, vector_store=vstore)
    assert res["status"] == "success"
    assert res["topics_count"] > 0
    assert res["is_dag"] is True

    tree = KnowledgeService.get_topic_tree(db_session)
    assert len(tree) > 0

    graph = KnowledgeService.get_graph(db_session)
    assert "nodes" in graph
    assert "edges" in graph
    assert graph["is_dag"] is True


def test_m3_grounded_tutor_and_citations(db_session):
    llm = MockLLM()
    vstore = LocalVectorStore()

    session = TutorService.create_session(db_session)
    assert session.id is not None

    res = TutorService.answer_query(
        db=db_session,
        session_id=session.id,
        query="What is a graph and how do DAGs work?",
        llm=llm,
        vector_store=vstore,
    )

    assert "reply" in res
    assert res["session_id"] == session.id
    assert isinstance(res["citations"], list)
    assert res["grounded"] is True

    history = TutorService.get_session_history(db_session, session.id)
    assert len(history) == 2  # user + assistant

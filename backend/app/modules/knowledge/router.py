"""Knowledge Graph API Router.

Endpoints for structuring curriculum, viewing topic hierarchies, and traversing DAG learning paths.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_llm, get_vector_store
from app.llm.base import LLMClient
from app.models import Topic
from app.modules.knowledge.service import KnowledgeService
from app.vectorstore.base import VectorStore

router = APIRouter(prefix="/knowledge", tags=["Knowledge Graph"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    summary: Optional[str] = None
    level: int
    parent_id: Optional[int] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/build", response_model=Dict[str, Any])
def build_knowledge_base(
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
):
    """Build the hierarchical topics and prerequisite DAG from all ingested content units."""
    return KnowledgeService.build_knowledge_base(db, llm, vector_store=vstore)


@router.get("/tree", response_model=List[Dict[str, Any]])
def get_topic_tree(db: Session = Depends(get_db)):
    """Get the hierarchical topic and concept tree."""
    return KnowledgeService.get_topic_tree(db)


@router.get("/graph", response_model=Dict[str, Any])
def get_graph(db: Session = Depends(get_db)):
    """Get the full prerequisite DAG with nodes, edges, and topological sort."""
    return KnowledgeService.get_graph(db)


@router.get("/path/{topic_id}", response_model=List[Dict[str, Any]])
def get_learning_path(topic_id: int, db: Session = Depends(get_db)):
    """Get prerequisite path ordered topologically to reach the target concept."""
    return KnowledgeService.get_learning_path(db, topic_id)


@router.get("/topics", response_model=List[TopicOut])
def list_topics(db: Session = Depends(get_db)):
    """List all extracted topics and concepts."""
    return db.query(Topic).all()


@router.get("/topics/{topic_id}", response_model=Dict[str, Any])
def get_topic_details(topic_id: int, db: Session = Depends(get_db)):
    """Get topic details, its prerequisites, and linked source units."""
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    prereqs = [p.prereq.name for p in topic.prerequisites if p.prereq]
    units = [
        {
            "id": ut.unit.id,
            "text": ut.unit.text[:200],
            "page": ut.unit.page,
            "slide_no": ut.unit.slide_no,
            "confidence": ut.confidence,
        }
        for ut in topic.unit_topics
        if ut.unit
    ]

    return {
        "id": topic.id,
        "name": topic.name,
        "summary": topic.summary,
        "level": topic.level,
        "parent_id": topic.parent_id,
        "prerequisites": prereqs,
        "linked_units": units,
    }

"""Tutor API Router.

Endpoints for interactive grounded tutoring, session creation, and conversation history.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_llm, get_vector_store
from app.llm.base import LLMClient
from app.modules.tutor.service import TutorService
from app.vectorstore.base import VectorStore

router = APIRouter(prefix="/tutor", tags=["Tutor"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    query: str
    student_id: Optional[int] = None
    strict_grounding: bool = False


class CreateSessionRequest(BaseModel):
    student_id: Optional[int] = None
    scope_topic_ids: Optional[List[int]] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/session", response_model=Dict[str, Any])
def create_chat_session(
    payload: Optional[CreateSessionRequest] = None,
    db: Session = Depends(get_db),
):
    """Create a new tutoring session."""
    student_id = payload.student_id if payload else None
    scope_topic_ids = payload.scope_topic_ids if payload else None
    session = TutorService.create_session(db, student_id=student_id, scope_topic_ids=scope_topic_ids)
    return {"session_id": session.id, "created_at": session.created_at}


@router.post("/chat", response_model=Dict[str, Any])
def send_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
):
    """Ask a question to the AI tutor and receive a source-grounded response with citations."""
    session_id = payload.session_id or 0
    return TutorService.answer_query(
        db=db,
        session_id=session_id,
        query=payload.query,
        llm=llm,
        vector_store=vstore,
        strict_grounding=payload.strict_grounding,
    )


@router.get("/sessions/{session_id}/messages", response_model=List[Dict[str, Any]])
def get_session_messages(session_id: int, db: Session = Depends(get_db)):
    """Retrieve message history and citations for a tutoring session."""
    return TutorService.get_session_history(db, session_id)

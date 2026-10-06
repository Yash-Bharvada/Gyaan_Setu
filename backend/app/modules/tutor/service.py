"""Tutor Service.

Coordinates multi-turn dialogue, hybrid retrieval, relevance gating,
LLM response synthesis with grounded source citations, and DB persistence.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.llm.base import LLMClient
from app.models import ChatMessage, ChatSession, Student, Unit
from app.modules.tutor.citations import extract_citations_from_text, format_unit_citation
from app.modules.tutor.gate import RelevanceGate
from app.modules.tutor.prompts import OUTSIDE_KNOWLEDGE_DISCLAIMER, REFUSAL_RESPONSE, TUTOR_SYSTEM_PROMPT
from app.modules.tutor.retrieval import HybridRetriever
from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)


class TutorService:
    @staticmethod
    def create_session(
        db: Session,
        student_id: Optional[int] = None,
        scope_topic_ids: Optional[List[int]] = None,
    ) -> ChatSession:
        """Create a new tutoring chat session."""
        session = ChatSession(
            student_id=student_id,
            scope_topic_ids=json.dumps(scope_topic_ids or []),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def answer_query(
        db: Session,
        session_id: int,
        query: str,
        llm: LLMClient,
        vector_store: VectorStore,
        strict_grounding: bool = False,
    ) -> Dict[str, Any]:
        """Process a user query, retrieve grounded source units, and generate an answer."""
        session = db.get(ChatSession, session_id)
        if not session:
            # Create session on the fly if not found
            session = TutorService.create_session(db)
            session_id = session.id

        # 1. Save student query
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=query,
        )
        db.add(user_msg)
        db.commit()

        # 2. Retrieve relevant source units (Hybrid BM25 + Vector)
        units = HybridRetriever.retrieve(
            query=query,
            db=db,
            llm=llm,
            vector_store=vector_store,
            top_k=4,
        )

        # 3. Check Relevance Gate
        gate_res = RelevanceGate.evaluate(query, units, llm, strict_grounding=strict_grounding)
        action = gate_res.get("action", "answer")

        # Handle strict refusal if irrelevant
        if action == "refuse" and not units:
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=REFUSAL_RESPONSE,
                citations=json.dumps([]),
                grounded=False,
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
            return {
                "session_id": session.id,
                "message_id": assistant_msg.id,
                "reply": REFUSAL_RESPONSE,
                "citations": [],
                "grounded": False,
                "action": "refusal",
            }

        # 4. Prepare Context & Citations
        available_citations = [format_unit_citation(u) for u in units]
        context_blocks = []
        for cit, u in zip(available_citations, units):
            context_blocks.append(f"--- {cit['citation_label']} ---\n{u.get('text', '')}")

        context_str = "\n\n".join(context_blocks)
        system_prompt = TUTOR_SYSTEM_PROMPT.format(context=context_str if context_str else "No course units uploaded yet.")

        # Build chat history for context
        past_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).limit(8).all()
        history_formatted = "\n".join([f"{m.role.capitalize()}: {m.content}" for m in past_msgs])

        user_prompt = f"Student Conversation History:\n{history_formatted}\n\nStudent Query: {query}\n\nTutor Explanation:"

        # 5. Generate LLM response
        try:
            answer_text = llm.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3,
            )
        except Exception as exc:
            logger.error("LLM tutor generation error: %s", exc)
            answer_text = f"Here is what the course material explains about this: {units[0]['text'][:300] if units else 'Please refer to your study guide.'}"

        is_grounded = bool(units)
        if action == "outside_knowledge_needed" and not units:
            answer_text += OUTSIDE_KNOWLEDGE_DISCLAIMER
            is_grounded = False

        used_citations = extract_citations_from_text(answer_text, available_citations)

        # 6. Save assistant message
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer_text,
            citations=json.dumps(used_citations),
            grounded=is_grounded,
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return {
            "session_id": session.id,
            "message_id": assistant_msg.id,
            "reply": answer_text,
            "citations": used_citations,
            "grounded": is_grounded,
            "gate_evaluation": gate_res,
        }

    @staticmethod
    def get_session_history(db: Session, session_id: int) -> List[Dict[str, Any]]:
        """Get all messages in a chat session."""
        session = db.get(ChatSession, session_id)
        if not session:
            raise NotFoundError(f"Session {session_id} not found")

        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": json.loads(m.citations) if m.citations else [],
                "grounded": m.grounded,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]

"""Assessment Service.

Orchestrates question bank generation, cross-model verification, adaptive quiz creation,
and assessment submission with automatic BKT mastery updates.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.llm.base import LLMClient
from app.models import (
    Assessment,
    AssessmentItem,
    AssessmentKind,
    Mastery,
    Question,
    QuestionType,
    Student,
    Topic,
    Unit,
)
from app.modules.assessment.generator import QuestionGenerator
from app.modules.assessment.grader import AssessmentGrader
from app.modules.assessment.verifier import QuestionVerifier
from app.modules.learner.service import LearnerService

logger = logging.getLogger(__name__)


class AssessmentService:
    @staticmethod
    def generate_questions_for_topic(
        db: Session,
        topic_id: int,
        llm: LLMClient,
        verifier_llm: Optional[LLMClient] = None,
        count: int = 2,
    ) -> List[Question]:
        """Generate and verify assessment questions for a specific topic."""
        topic = db.get(Topic, topic_id)
        if not topic:
            raise NotFoundError(f"Topic {topic_id} not found")

        units = [ut.unit for ut in topic.unit_topics if ut.unit]
        if not units:
            units = db.query(Unit).limit(3).all()

        v_llm = verifier_llm or llm
        generated_records: List[Question] = []

        for q_type in [QuestionType.mcq, QuestionType.short]:
            raw_qs = QuestionGenerator.generate_questions(
                units=units,
                topic=topic,
                llm=llm,
                question_type=q_type,
                difficulty=3,
            )

            for q_data in raw_qs:
                # Cross-model verification
                is_valid, strength, critique = QuestionVerifier.verify_question(q_data, v_llm)

                # Check duplicate stem
                stem = q_data.get("stem", "").strip()
                existing = db.query(Question).filter(Question.stem == stem).first()
                if existing:
                    continue

                q_obj = Question(
                    type=QuestionType(q_data.get("type", q_type.value)),
                    stem=stem,
                    options=json.dumps(q_data.get("options")) if q_data.get("options") else None,
                    answer_key=str(q_data.get("answer_key", "")),
                    explanation=q_data.get("explanation", ""),
                    distractor_rationales=json.dumps(q_data.get("distractor_rationales")) if q_data.get("distractor_rationales") else None,
                    topic_id=topic.id,
                    difficulty=q_data.get("difficulty", 3),
                    verified=is_valid,
                    verification_strength=strength,
                )
                db.add(q_obj)
                generated_records.append(q_obj)

        db.commit()
        all_topic_questions = db.query(Question).filter(Question.topic_id == topic.id).all()
        return all_topic_questions

    @staticmethod
    def create_quiz(
        db: Session,
        student_id: int,
        kind: AssessmentKind = AssessmentKind.quiz,
        num_questions: int = 5,
        topic_ids: Optional[List[int]] = None,
    ) -> Assessment:
        """Create an adaptive quiz prioritizing topics with low BKT mastery."""
        student = db.get(Student, student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")

        # Select target questions
        query = db.query(Question)
        if topic_ids:
            query = query.filter(Question.topic_id.in_(topic_ids))

        all_questions = query.all()

        if not all_questions:
            # Generate a few placeholder questions if none in bank
            topics = db.query(Topic).all()
            for t in topics[:2]:
                from app.llm.mock import MockLLM
                AssessmentService.generate_questions_for_topic(db, t.id, MockLLM())
            all_questions = db.query(Question).all()

        # Score questions by student need (lower mastery = higher priority)
        mastery_map = {m.topic_id: m.p_known for m in student.mastery}

        def question_priority(q: Question) -> float:
            p_k = mastery_map.get(q.topic_id, 0.3)
            # We want items with p_k close to 0.5 or lower (ZPD - Zone of Proximal Development)
            return 1.0 - abs(p_k - 0.5)

        sorted_questions = sorted(all_questions, key=question_priority, reverse=True)
        selected = sorted_questions[:num_questions]

        assessment = Assessment(
            student_id=student_id,
            kind=kind,
            status="open",
            adaptive=True,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        for q in selected:
            item = AssessmentItem(
                assessment_id=assessment.id,
                question_id=q.id,
            )
            db.add(item)

        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def submit_quiz(
        db: Session,
        assessment_id: int,
        responses: List[Dict[str, Any]],  # [{"question_id": int, "response": str, "time_taken_secs": float}]
        llm: LLMClient,
    ) -> Dict[str, Any]:
        """Grade all items, calculate score, update student BKT mastery, and return detailed report."""
        assessment = db.get(Assessment, assessment_id)
        if not assessment:
            raise NotFoundError(f"Assessment {assessment_id} not found")

        resp_map = {r["question_id"]: r for r in responses}
        total_score = 0.0
        graded_items = []
        topic_deltas = {}

        for item in assessment.items:
            q = item.question
            user_resp_data = resp_map.get(q.id, {})
            user_text = user_resp_data.get("response", "")
            time_taken = user_resp_data.get("time_taken_secs", 0.0)

            grade_res = AssessmentGrader.grade_item(q, user_text, llm)
            item.response = user_text
            item.score = grade_res["score"]
            item.feedback = json.dumps(grade_res)
            item.time_taken_secs = time_taken
            item.graded_at = datetime.utcnow()

            total_score += item.score

            # Update BKT mastery
            if q.topic_id:
                m_before = db.query(Mastery).filter(
                    Mastery.student_id == assessment.student_id,
                    Mastery.topic_id == q.topic_id,
                ).first()
                p_before = m_before.p_known if m_before else 0.30

                m_after = LearnerService.record_attempt(
                    db=db,
                    student_id=assessment.student_id,
                    topic_id=q.topic_id,
                    correct=grade_res["is_correct"],
                )
                topic_obj = db.get(Topic, q.topic_id)
                topic_deltas[q.topic_id] = {
                    "topic_name": topic_obj.name if topic_obj else f"Topic {q.topic_id}",
                    "p_before": p_before,
                    "p_after": m_after.p_known,
                }

            graded_items.append({
                "question_id": q.id,
                "stem": q.stem,
                "type": q.type.value,
                "student_response": user_text,
                "correct_answer": q.answer_key,
                "score": item.score,
                "is_correct": grade_res["is_correct"],
                "feedback": grade_res["feedback"],
            })

        final_percentage = round((total_score / max(1, len(assessment.items))) * 100, 1)
        assessment.score = final_percentage
        assessment.status = "submitted"
        assessment.submitted_at = datetime.utcnow()

        report = {
            "assessment_id": assessment.id,
            "score_percentage": final_percentage,
            "total_items": len(assessment.items),
            "items": graded_items,
            "mastery_updates": list(topic_deltas.values()),
        }
        assessment.report = json.dumps(report)
        db.commit()

        return report

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
                count=count,
            )

            for q_data in raw_qs:
                # Cross-model verification
                is_valid, strength, critique = QuestionVerifier.verify_question(q_data, v_llm)

                # Check duplicate stem
                stem = q_data.get("stem", "").strip()
                if not stem:
                    continue
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
        """Create an adaptive quiz prioritizing topics with low BKT mastery, generating enough questions to satisfy requested count."""
        student = db.get(Student, student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")

        # Query matching questions
        def get_matching_questions():
            q = db.query(Question)
            if topic_ids:
                q = q.filter(Question.topic_id.in_(topic_ids))
            return q.all()

        all_questions = get_matching_questions()

        # If existing question count is below requested count, generate real questions
        if len(all_questions) < num_questions:
            from app.llm.groq import GroqClient
            llm_inst = GroqClient()

            # Rank topics: if topic_ids given, use them; else sort topics by student's mastery gap
            mastery_map = {m.topic_id: m.p_known for m in student.mastery}
            all_topics = db.query(Topic).all()

            if topic_ids:
                target_topics = [t for t in all_topics if t.id in topic_ids]
            else:
                target_topics = sorted(all_topics, key=lambda t: mastery_map.get(t.id, 0.0))

            needed = num_questions - len(all_questions)
            questions_per_topic = max(2, min(5, (needed + len(target_topics) - 1) // max(1, len(target_topics))))

            for t in target_topics:
                if len(all_questions) >= num_questions:
                    break
                try:
                    AssessmentService.generate_questions_for_topic(
                        db=db,
                        topic_id=t.id,
                        llm=llm_inst,
                        count=questions_per_topic,
                    )
                    all_questions = get_matching_questions()
                except Exception as exc:
                    logger.warning("Question generation failed for topic %s: %s", t.id, exc)

            # If still short (e.g. single topic with high question count requested), generate across different difficulties
            if len(all_questions) < num_questions and target_topics:
                for diff in [1, 5]:
                    if len(all_questions) >= num_questions:
                        break
                    for t in target_topics:
                        if len(all_questions) >= num_questions:
                            break
                        units = [ut.unit for ut in t.unit_topics if ut.unit]
                        if not units:
                            units = db.query(Unit).limit(3).all()
                        for q_type in [QuestionType.mcq, QuestionType.short]:
                            try:
                                raw_qs = QuestionGenerator.generate_questions(
                                    units=units,
                                    topic=t,
                                    llm=llm_inst,
                                    question_type=q_type,
                                    difficulty=diff,
                                    count=2,
                                )
                                for q_data in raw_qs:
                                    stem = q_data.get("stem", "").strip()
                                    if not stem or db.query(Question).filter(Question.stem == stem).first():
                                        continue
                                    q_obj = Question(
                                        type=QuestionType(q_data.get("type", q_type.value)),
                                        stem=stem,
                                        options=json.dumps(q_data.get("options")) if q_data.get("options") else None,
                                        answer_key=str(q_data.get("answer_key", "")),
                                        explanation=q_data.get("explanation", ""),
                                        distractor_rationales=json.dumps(q_data.get("distractor_rationales")) if q_data.get("distractor_rationales") else None,
                                        topic_id=t.id,
                                        difficulty=diff,
                                        verified=True,
                                        verification_strength="strong",
                                    )
                                    db.add(q_obj)
                                db.commit()
                            except Exception as exc:
                                logger.warning("Multi-difficulty question gen error: %s", exc)
                        all_questions = get_matching_questions()

            # If STILL short because a single narrow topic has no more questions, expand to curriculum questions
            if len(all_questions) < num_questions and topic_ids:
                extra_questions = db.query(Question).filter(~Question.id.in_([q.id for q in all_questions])).all()
                all_questions.extend(extra_questions[:num_questions - len(all_questions)])

        # Score questions by student need (lower mastery = higher priority in ZPD)
        mastery_map = {m.topic_id: m.p_known for m in student.mastery}

        def question_priority(q: Question) -> float:
            p_k = mastery_map.get(q.topic_id, 0.3)
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

"""Integration & Unit Tests for Modules M4 (Learner BKT), M5 (Adaptive Assessment), and M6 (Evaluation)."""
import pytest
from app.llm.mock import MockLLM
from app.vectorstore.local_store import LocalVectorStore
from app.modules.learner.bkt import BKTEngine
from app.modules.learner.service import LearnerService
from app.modules.assessment.service import AssessmentService
from app.modules.evaluation.runner import RAGEvaluator
from app.modules.evaluation.simulator import StudentSimulator
from app.models import Topic, Question, Assessment, Mastery


def test_m4_bkt_updates_and_learner_service(db_session):
    # Test BKT mathematical formula
    p_init = 0.30
    p_after_correct = BKTEngine.update(p_init, correct=True)
    assert p_after_correct > p_init

    p_after_wrong = BKTEngine.update(p_init, correct=False)
    assert p_after_wrong < p_init

    # Test Student profile and attempts
    student = LearnerService.create_student(db_session, name="Jane Doe", daily_minutes=45)
    assert student.id is not None

    topic = db_session.query(Topic).first()
    if not topic:
        topic = Topic(name="Data Structures", level=0)
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

    mastery = LearnerService.record_attempt(db_session, student_id=student.id, topic_id=topic.id, correct=True)
    assert mastery.p_known > 0.30
    assert mastery.n_attempts == 1

    overview = LearnerService.get_mastery_overview(db_session, student_id=student.id)
    assert len(overview) >= 1


def test_m5_adaptive_assessment_and_grading(db_session):
    llm = MockLLM()
    student = db_session.query(Topic).first()
    student_obj = LearnerService.create_student(db_session, name="Bob Smith")

    topic = db_session.query(Topic).first()
    questions = AssessmentService.generate_questions_for_topic(db_session, topic_id=topic.id, llm=llm)
    assert len(questions) >= 1
    assert questions[0].verified is True

    quiz = AssessmentService.create_quiz(db_session, student_id=student_obj.id, num_questions=2)
    assert quiz.id is not None
    assert len(quiz.items) >= 1

    # Submit quiz
    responses = [{"question_id": item.question_id, "response": item.question.answer_key, "time_taken_secs": 15.0} for item in quiz.items]
    report = AssessmentService.submit_quiz(db_session, assessment_id=quiz.id, responses=responses, llm=llm)

    assert report["score_percentage"] == 100.0
    assert len(report["items"]) == len(quiz.items)


def test_m6_system_evaluation_rag_and_simulation(db_session):
    llm = MockLLM()
    vstore = LocalVectorStore()

    eval_run = RAGEvaluator.run_benchmark(db_session, llm=llm, vector_store=vstore, test_queries=["What is a graph?"])
    assert eval_run.id is not None
    assert eval_run.kind == "rag"

    sim_res = StudentSimulator.simulate_trajectory(db_session, persona="average_learner", days=3)
    assert sim_res["days_simulated"] == 3
    assert len(sim_res["trajectory"]) == 3

"""Spaced Study Schedule Planner module.

Synthesizes student goals, daily study time budgets, exam deadlines,
DAG topological ordering, and forgetting curves to generate an optimal revision calendar.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import ActivityKind, Mastery, Schedule, Student, Topic
from app.modules.knowledge.graph import KnowledgeDAG
from app.modules.scheduler.forgetting import ForgettingModel

logger = logging.getLogger(__name__)


class StudyPlanner:
    @staticmethod
    def generate_schedule(
        db: Session,
        student_id: int,
        target_days: Optional[int] = None,
        daily_minutes: Optional[int] = None,
    ) -> Schedule:
        """Generate a multi-day personalized study schedule."""
        student = db.get(Student, student_id)
        if not student:
            raise Exception(f"Student {student_id} not found")

        minutes_per_day = daily_minutes or student.daily_minutes or 30
        now = datetime.utcnow()

        if target_days:
            num_days = max(1, target_days)
        elif student.exam_date:
            delta = (student.exam_date - now).days
            num_days = max(1, min(60, delta))
        else:
            num_days = 14

        # 1. Get curriculum in prerequisite order
        dag = KnowledgeDAG()
        dag.build_from_db(db)
        topo_topic_ids = dag.get_topological_order()

        # 2. Get decay status and mastery
        decay_info = {d["topic_id"]: d for d in ForgettingModel.get_decayed_mastery(db, student_id)}

        # Separate topics into review vs new learning
        topics_to_review = [tid for tid in topo_topic_ids if decay_info.get(tid, {}).get("needs_urgent_review", False)]
        topics_to_learn = [tid for tid in topo_topic_ids if tid not in topics_to_review]

        daily_items = []
        rev_idx = 0
        learn_idx = 0

        for day in range(1, num_days + 1):
            day_date = (now + timedelta(days=day - 1)).strftime("%Y-%m-%d")
            slots = []
            remaining_mins = minutes_per_day

            # Allocate Review slot if review topics exist
            if topics_to_review and rev_idx < len(topics_to_review) and remaining_mins >= 15:
                t_id = topics_to_review[rev_idx % len(topics_to_review)]
                rev_idx += 1
                topic = db.get(Topic, t_id)
                alloc_mins = min(15, remaining_mins)
                slots.append({
                    "activity": ActivityKind.review.value,
                    "topic_id": t_id,
                    "topic_name": topic.name if topic else f"Topic {t_id}",
                    "allocated_minutes": alloc_mins,
                    "description": f"Spaced review to combat memory decay.",
                })
                remaining_mins -= alloc_mins

            # Allocate New Learn slot
            if topics_to_learn and learn_idx < len(topics_to_learn) and remaining_mins >= 15:
                t_id = topics_to_learn[learn_idx % len(topics_to_learn)]
                learn_idx += 1
                topic = db.get(Topic, t_id)
                alloc_mins = min(20, remaining_mins)
                slots.append({
                    "activity": ActivityKind.learn.value,
                    "topic_id": t_id,
                    "topic_name": topic.name if topic else f"Topic {t_id}",
                    "allocated_minutes": alloc_mins,
                    "description": f"Master new prerequisite concepts.",
                })
                remaining_mins -= alloc_mins

            # Allocate Practice Quiz slot if minutes remain
            if remaining_mins >= 10:
                slots.append({
                    "activity": ActivityKind.quiz.value,
                    "topic_id": topo_topic_ids[day % len(topo_topic_ids)] if topo_topic_ids else None,
                    "topic_name": "Active Recall Check",
                    "allocated_minutes": remaining_mins,
                    "description": "5-minute diagnostic quiz.",
                })

            daily_items.append({
                "day": day,
                "date": day_date,
                "total_minutes": minutes_per_day,
                "sessions": slots,
            })

        schedule = Schedule(
            student_id=student_id,
            version=1,
            items=json.dumps(daily_items),
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return schedule

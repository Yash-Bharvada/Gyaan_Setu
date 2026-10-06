"""Knowledge Base Service.

Orchestrates topic hierarchy extraction, prerequisite DAG construction,
concept tagging, and curriculum traversal.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.llm.base import LLMClient
from app.models import Prerequisite, Topic, Unit, UnitTopic
from app.modules.knowledge.graph import KnowledgeDAG, infer_prerequisites_with_llm
from app.modules.knowledge.tagging import ConceptTagger
from app.modules.knowledge.topics import TopicExtractor
from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)


class KnowledgeService:
    @staticmethod
    def build_knowledge_base(
        db: Session,
        llm: LLMClient,
        vector_store: Optional[VectorStore] = None,
    ) -> Dict[str, Any]:
        """Extract topics, build prerequisite DAG, and tag all content units."""
        units = db.query(Unit).all()
        if not units:
            raise AppError("No ingested units found to build knowledge base from.")

        # 1. Extract topics & concepts
        units_text = [u.text for u in units]
        extracted_topics = TopicExtractor.extract_topics(units_text, llm)

        created_topics: List[Topic] = []
        name_to_topic: Dict[str, Topic] = {}

        for t_data in extracted_topics:
            topic_name = t_data.get("name", "Untitled Topic")
            existing_t = db.query(Topic).filter(Topic.name == topic_name, Topic.level == 0).first()
            if not existing_t:
                parent_topic = Topic(
                    name=topic_name,
                    summary=t_data.get("summary", ""),
                    level=0,
                )
                db.add(parent_topic)
                db.commit()
                db.refresh(parent_topic)
            else:
                parent_topic = existing_t

            created_topics.append(parent_topic)
            name_to_topic[parent_topic.name.lower()] = parent_topic

            # Extract children concepts
            concepts = t_data.get("concepts", [])
            for c_data in concepts:
                c_name = c_data.get("name", "Untitled Concept")
                existing_c = db.query(Topic).filter(Topic.name == c_name, Topic.parent_id == parent_topic.id).first()
                if not existing_c:
                    child_topic = Topic(
                        name=c_name,
                        summary=c_data.get("summary", ""),
                        level=1,
                        parent_id=parent_topic.id,
                    )
                    db.add(child_topic)
                    db.commit()
                    db.refresh(child_topic)
                else:
                    child_topic = existing_c

                created_topics.append(child_topic)
                name_to_topic[child_topic.name.lower()] = child_topic

        # 2. Build DAG and Infer Prerequisites
        dag = KnowledgeDAG()
        dag.build_from_db(db)

        raw_prereqs = infer_prerequisites_with_llm(created_topics, llm)
        added_edges = 0

        for edge in raw_prereqs:
            t_name = edge.get("topic_name", "").lower()
            p_name = edge.get("prereq_name", "").lower()

            target_topic = name_to_topic.get(t_name)
            prereq_topic = name_to_topic.get(p_name)

            if target_topic and prereq_topic and target_topic.id != prereq_topic.id:
                if dag.add_edge_safe(
                    prereq_id=prereq_topic.id,
                    topic_id=target_topic.id,
                    confidence=edge.get("confidence", 1.0),
                    rationale=edge.get("rationale", ""),
                ):
                    existing_edge = db.query(Prerequisite).filter(
                        Prerequisite.topic_id == target_topic.id,
                        Prerequisite.prereq_id == prereq_topic.id,
                    ).first()
                    if not existing_edge:
                        db.add(Prerequisite(
                            topic_id=target_topic.id,
                            prereq_id=prereq_topic.id,
                            confidence=edge.get("confidence", 1.0),
                            rationale=edge.get("rationale", ""),
                        ))
                        added_edges += 1

        db.commit()

        # 3. Tag units to topics
        tagged_count = ConceptTagger.tag_units_to_topics(db, llm)

        # 4. Rebuild DAG to ensure fresh graph state
        dag.build_from_db(db)
        graph_data = dag.export_graph_data()

        return {
            "status": "success",
            "topics_count": len(created_topics),
            "prerequisites_added": added_edges,
            "unit_tags_created": tagged_count,
            "is_dag": graph_data["is_dag"],
            "topological_order": dag.get_topological_order(),
        }

    @staticmethod
    def get_topic_tree(db: Session) -> List[Dict[str, Any]]:
        """Get hierarchical topic tree."""
        root_topics = db.query(Topic).filter(Topic.parent_id == None).all()
        result = []
        for t in root_topics:
            result.append({
                "id": t.id,
                "name": t.name,
                "summary": t.summary,
                "level": t.level,
                "concepts": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "summary": c.summary,
                        "level": c.level,
                    }
                    for c in t.children
                ],
            })
        return result

    @staticmethod
    def get_graph(db: Session) -> Dict[str, Any]:
        """Return full knowledge prerequisite graph representation."""
        dag = KnowledgeDAG()
        dag.build_from_db(db)
        return dag.export_graph_data()

    @staticmethod
    def get_learning_path(db: Session, target_topic_id: int) -> List[Dict[str, Any]]:
        """Get prerequisite chain leading up to target_topic_id in topological order."""
        target = db.get(Topic, target_topic_id)
        if not target:
            raise NotFoundError(f"Topic {target_topic_id} not found")

        dag = KnowledgeDAG()
        dag.build_from_db(db)
        prereq_ids = set(dag.get_prerequisites(target_topic_id, recursive=True))
        prereq_ids.add(target_topic_id)

        topo_order = dag.get_topological_order()
        filtered_order = [tid for tid in topo_order if tid in prereq_ids]

        result = []
        for tid in filtered_order:
            t = db.get(Topic, tid)
            if t:
                result.append({
                    "id": t.id,
                    "name": t.name,
                    "summary": t.summary,
                    "level": t.level,
                    "is_target": (t.id == target_topic_id),
                })
        return result

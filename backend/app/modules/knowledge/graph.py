"""Knowledge Graph and Prerequisite DAG module.

Constructs, validates, and traverses the concept prerequisite Directed Acyclic Graph (DAG).
Uses networkx for cycle detection, topological sorting, and dependency chain resolution.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.llm.base import LLMClient
from app.models import Prerequisite, Topic

logger = logging.getLogger(__name__)

PREREQ_EXTRACTION_PROMPT = """Given the following list of academic topics/concepts:
{topics_list}

Determine the direct prerequisite relationships (which concept MUST be learned before another).
Return a valid JSON object matching this schema:
{{
  "edges": [
    {{
      "topic_name": "Advanced Concept",
      "prereq_name": "Basic Concept",
      "confidence": 0.95,
      "rationale": "Reason why basic concept is required first"
    }}
  ]
}}
"""


class KnowledgeDAG:
    def __init__(self):
        self.graph: nx.DiGraph = nx.DiGraph()

    def build_from_db(self, db: Session) -> nx.DiGraph:
        """Load topics and prerequisite edges from DB into the networkx graph."""
        self.graph.clear()
        topics = db.query(Topic).all()
        for t in topics:
            self.graph.add_node(
                t.id,
                name=t.name,
                summary=t.summary or "",
                level=t.level,
                parent_id=t.parent_id,
            )

        prereqs = db.query(Prerequisite).all()
        for p in prereqs:
            # Directed edge from prereq_id -> topic_id (prereq precedes topic)
            if self.graph.has_node(p.prereq_id) and self.graph.has_node(p.topic_id):
                self.graph.add_edge(
                    p.prereq_id,
                    p.topic_id,
                    confidence=p.confidence,
                    rationale=p.rationale or "",
                )

        return self.graph

    def add_edge_safe(
        self,
        prereq_id: int,
        topic_id: int,
        confidence: float = 1.0,
        rationale: str = "",
    ) -> bool:
        """Add a prerequisite edge only if it does NOT create a cycle."""
        if prereq_id == topic_id:
            return False

        self.graph.add_edge(prereq_id, topic_id, confidence=confidence, rationale=rationale)
        if not nx.is_directed_acyclic_graph(self.graph):
            # Rollback edge if it creates a cycle
            self.graph.remove_edge(prereq_id, topic_id)
            logger.warning("Prerequisite edge (%d -> %d) creates a cycle, skipped.", prereq_id, topic_id)
            return False
        return True

    def get_prerequisites(self, topic_id: int, recursive: bool = True) -> List[int]:
        """Get prerequisite topic IDs for a given topic."""
        if not self.graph.has_node(topic_id):
            return []
        if recursive:
            return list(nx.ancestors(self.graph, topic_id))
        else:
            return list(self.graph.predecessors(topic_id))

    def get_dependents(self, topic_id: int, recursive: bool = True) -> List[int]:
        """Get downstream topics that depend on this topic."""
        if not self.graph.has_node(topic_id):
            return []
        if recursive:
            return list(nx.descendants(self.graph, topic_id))
        else:
            return list(self.graph.successors(topic_id))

    def get_topological_order(self) -> List[int]:
        """Return full curriculum in valid prerequisite-first learning order."""
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            # Fallback if somehow cycle exists
            return list(self.graph.nodes())

    def export_graph_data(self) -> Dict[str, Any]:
        """Export graph nodes and edges for visualization / frontend flow maps."""
        nodes = []
        for n, data in self.graph.nodes(data=True):
            nodes.append({
                "id": n,
                "name": data.get("name", f"Topic {n}"),
                "summary": data.get("summary", ""),
                "level": data.get("level", 0),
                "parent_id": data.get("parent_id"),
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,  # prereq
                "target": v,  # topic
                "confidence": data.get("confidence", 1.0),
                "rationale": data.get("rationale", ""),
            })

        return {"nodes": nodes, "edges": edges, "is_dag": nx.is_directed_acyclic_graph(self.graph)}


def infer_prerequisites_with_llm(
    topics: List[Topic],
    llm: LLMClient,
) -> List[Dict[str, Any]]:
    """Use LLM reasoning to infer prerequisite links between topics."""
    if len(topics) < 2:
        return []

    topic_names = [f"- {t.name} (ID: {t.id}): {t.summary or ''}" for t in topics]
    prompt = PREREQ_EXTRACTION_PROMPT.format(topics_list="\n".join(topic_names[:30]))

    try:
        res = llm.generate_json(prompt)
        if isinstance(res, dict) and "edges" in res:
            return res["edges"]
    except Exception as exc:
        logger.warning("LLM prerequisite inference fallback: %s", exc)

    # Heuristic chain if LLM fails: lower level -> higher level, earlier index -> later index
    edges = []
    for i in range(len(topics) - 1):
        edges.append({
            "topic_name": topics[i + 1].name,
            "prereq_name": topics[i].name,
            "confidence": 0.8,
            "rationale": "Sequential curriculum dependency",
        })
    return edges

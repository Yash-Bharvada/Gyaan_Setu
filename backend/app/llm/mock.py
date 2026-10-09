"""
Deterministic MockLLM for offline tests — never touches any external API.

Behaviour
---------
- ``generate()``         → echoes back a labelled stub string
- ``generate_json()``    → returns a schema-specific canned Pydantic object
- ``embed()``            → hash-based deterministic float vectors (length = dim)
- ``describe_image()``   → canned description string
- ``transcribe()``       → synthetic timestamped segments from a counter
- ``get_usage()``        → always-zero counters
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel

from app.llm.base import LLMClient


_DEFAULT_DIM = 384


def _hash_embed(text: str, dim: int = _DEFAULT_DIM) -> List[float]:
    """Deterministic pseudo-embedding based on SHA-256 of text."""
    digest = hashlib.sha256(text.encode()).digest()  # 32 bytes
    # Repeat until we have enough values, then normalise
    repeated = (digest * (dim // 32 + 1))[:dim]
    raw = [b / 255.0 - 0.5 for b in repeated]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [x / norm for x in raw]


class MockLLM(LLMClient):
    """100 % offline mock — safe to use from any test."""

    PROVIDER: str = "mock"

    def __init__(self, dim: int = _DEFAULT_DIM):
        self._dim = dim
        self._calls: Dict[str, int] = {}

    def _count(self, key: str):
        self._calls[key] = self._calls.get(key, 0) + 1

    # ── Text generation ──────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        bypass_cache: bool = False,
    ) -> str:
        self._count(f"generate_{role}")
        return f"[MOCK-{role.upper()}] response to: {prompt[:60]}"

    def generate_json(
        self,
        prompt: str,
        schema: Type[BaseModel] | None = None,
        system: str | None = None,
        role: Literal["generator", "verifier"] = "generator",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        repair_retry: int = 1,
        bypass_cache: bool = False,
    ) -> Any:
        self._count(f"generate_json_{role}")
        if schema is not None:
            # Build a minimal valid instance by filling required fields with sensible stubs
            fields = schema.model_fields
            data: Dict[str, Any] = {}
            for name, field_info in fields.items():
                ann = field_info.annotation
                origin = getattr(ann, "__origin__", None)
                args = getattr(ann, "__args__", ())
                if origin is type(None):
                    data[name] = None
                    continue
                if origin is not None and type(None) in args:
                    inner = next((a for a in args if a is not type(None)), str)
                    ann = inner

                if ann is str:
                    data[name] = f"mock_{name}"
                elif ann is int:
                    data[name] = 1
                elif ann is float:
                    data[name] = 1.0
                elif ann is bool:
                    data[name] = True
                elif ann is list or (origin is list):
                    data[name] = []
                elif ann is dict or (origin is dict):
                    data[name] = {}
                else:
                    data[name] = None
            return schema.model_validate(data)

        p_lower = prompt.lower()
        if "topic" in p_lower or "concept" in p_lower:
            return {
                "topics": [
                    {
                        "name": "Foundational Graph Theory",
                        "summary": "Core graph models, vertices, edges, directed and undirected topologies.",
                        "level": 0,
                    },
                    {
                        "name": "Topological Sorting & DAGs",
                        "summary": "Linear node ordering in directed acyclic graphs and prerequisite chains.",
                        "level": 1,
                    },
                    {
                        "name": "Shortest Path Optimizations",
                        "summary": "Dijkstra and Bellman-Ford path relaxation algorithms.",
                        "level": 2,
                    },
                ]
            }
        elif "question" in p_lower:
            return {
                "questions": [
                    {
                        "type": "mcq",
                        "stem": "Which property is required for a directed graph to admit a valid topological ordering?",
                        "options": [
                            "The graph must be a Directed Acyclic Graph (DAG) with no directed cycles.",
                            "The graph must be strongly connected with bidirectional edges.",
                            "The graph must be complete with edge weights summing to zero.",
                            "The graph must have an odd number of vertices.",
                        ],
                        "answer_key": "The graph must be a Directed Acyclic Graph (DAG) with no directed cycles.",
                        "explanation": "Topological sorting requires that for every directed edge (u, v), u appears before v. If a cycle exists, this linear order is impossible.",
                        "distractor_rationales": {
                            "1": "Strong connectivity implies cycles, which prevents topological sort.",
                            "2": "Completeness or edge weights do not govern acyclicity.",
                            "3": "Parity of vertex count is irrelevant to DAG ordering.",
                        },
                        "difficulty": 3,
                    },
                    {
                        "type": "short",
                        "stem": "Explain why Dijkstra's algorithm fails or produces incorrect results on graphs with negative-weight edges.",
                        "answer_key": "Dijkstra greedily marks vertices as finalized once popped from the priority queue under the assumption that path costs only increase. Negative edges violate this monotonic greedy property.",
                        "explanation": "Bellman-Ford is needed for negative weights because it relaxes all edges |V|-1 times.",
                        "difficulty": 4,
                    },
                ]
            }
        elif "prerequisite" in p_lower or "edge" in p_lower:
            return {
                "edges": [
                    {
                        "topic_name": "Topological Sorting & DAGs",
                        "prereq_name": "Foundational Graph Theory",
                        "confidence": 0.95,
                        "rationale": "DAG topological sorting depends on understanding vertices and directed edges.",
                    },
                    {
                        "topic_name": "Shortest Path Optimizations",
                        "prereq_name": "Topological Sorting & DAGs",
                        "confidence": 0.88,
                        "rationale": "DAG shortest path relaxations build directly upon topological ordering.",
                    },
                ]
            }
        elif "gate" in p_lower or "is_relevant" in p_lower:
            return {
                "is_relevant": True,
                "confidence": 0.92,
                "rationale": "Retrieved course materials provide direct grounding for this inquiry.",
                "action": "answer",
            }
        elif "flashcard" in p_lower:
            return {
                "flashcards": [
                    {
                        "front": "What is the time complexity of topological sorting using Kahn's algorithm or DFS?",
                        "back": "O(V + E), where V is the number of vertices and E is the number of edges, as each vertex and edge is processed once.",
                    },
                    {
                        "front": "Under what condition does Bellman-Ford terminate with a report of failure?",
                        "back": "When a negative-weight cycle is detected during the |V|-th relaxation pass.",
                    },
                ]
            }
        elif "audio" in p_lower or "brief" in p_lower:
            return {
                "topic": "Graph Algorithms Review",
                "estimated_duration_secs": 120,
                "sections": {
                    "intro": "Welcome to your Gyaan Setu revision brief on Graph Algorithms.",
                    "core_concepts": "Remember that a DAG has no directed cycles, enabling topological sorting in O(V + E). For shortest paths, use Dijkstra when weights are positive, and Bellman-Ford when negative weights may occur.",
                    "rapid_check": "Quick pause: what data structure does Dijkstra use to extract min-distance nodes efficiently?",
                    "mnemonic_wrap": "Recall: No Cycles, Valid DAG. Priority Queue, Dijkstra's Bag.",
                },
                "full_spoken_script": "Welcome to your Gyaan Setu revision brief on Graph Algorithms. Remember that a DAG has no directed cycles, enabling topological sorting in O(V + E). For shortest paths, use Dijkstra when weights are positive, and Bellman-Ford when negative weights may occur. Quick pause: what data structure does Dijkstra use to extract min-distance nodes efficiently? A min-priority queue. Keep learning and revising!",
            }
        elif "verify" in p_lower or "rubric" in p_lower:
            return {
                "is_valid": True,
                "verification_strength": 0.95,
                "score": 1.0,
                "feedback": "Correct and well-formulated based on reference syllabus.",
            }
        return {"status": "ok", "result": "mock_response"}

    # ── Embeddings ───────────────────────────────────────────────────────────

    def embed(self, texts: List[str]) -> List[List[float]]:
        self._count("embed")
        return [_hash_embed(t, self._dim) for t in texts]

    # ── Vision ───────────────────────────────────────────────────────────────

    def describe_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe this image concisely and factually.",
        bypass_cache: bool = False,
    ) -> str:
        self._count("describe_image")
        digest = hashlib.md5(image_bytes).hexdigest()[:8]
        return f"[MOCK] Image description for hash={digest}"

    # ── Transcription ────────────────────────────────────────────────────────

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> List[Dict[str, Any]]:
        self._count("transcribe")
        # Return two synthetic 30-second segments
        return [
            {"text": "Mock transcript segment one.", "start": 0.0, "end": 30.0},
            {"text": "Mock transcript segment two.", "start": 30.0, "end": 60.0},
        ]

    # ── Usage ────────────────────────────────────────────────────────────────

    def get_usage(self) -> Dict[str, Any]:
        return {"provider": "mock", "calls": self._calls, "cost": 0.0}

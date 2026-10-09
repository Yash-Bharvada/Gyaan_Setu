"""Evaluation API Router.

Endpoints for RAG quality metrics benchmarking and synthetic student trajectory simulations.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_llm, get_vector_store
from app.llm.base import LLMClient
from app.models import EvalRun
from app.modules.evaluation.runner import RAGEvaluator
from app.modules.evaluation.simulator import StudentSimulator
from app.vectorstore.base import VectorStore

router = APIRouter(prefix="/eval", tags=["Evaluation"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class RAGBenchmarkRequest(BaseModel):
    test_queries: Optional[List[str]] = None


class SimulationRequest(BaseModel):
    persona: Optional[str] = "average_learner"
    days: Optional[int] = 7


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/rag", response_model=Dict[str, Any])
def run_rag_benchmark(
    payload: Optional[RAGBenchmarkRequest] = None,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    vstore: VectorStore = Depends(get_vector_store),
):
    """Run RAG evaluation benchmark across test queries."""
    queries = payload.test_queries if payload else None
    eval_run = RAGEvaluator.run_benchmark(db=db, llm=llm, vector_store=vstore, test_queries=queries)
    return {
        "eval_run_id": eval_run.id,
        "kind": eval_run.kind,
        "metrics": json.loads(eval_run.metrics) if eval_run.metrics else {},
    }


@router.post("/simulate", response_model=Dict[str, Any])
def run_student_simulation(
    payload: Optional[SimulationRequest] = None,
    db: Session = Depends(get_db),
):
    """Run synthetic student learning trajectory simulation."""
    persona = payload.persona if payload else "average_learner"
    days = payload.days if payload else 7
    eval_run = StudentSimulator.run_and_save_simulation(db=db, persona=persona, days=days)
    return {
        "eval_run_id": eval_run.id,
        "kind": eval_run.kind,
        "metrics": json.loads(eval_run.metrics) if eval_run.metrics else {},
    }


@router.get("/runs", response_model=List[Dict[str, Any]])
def list_eval_runs(db: Session = Depends(get_db)):
    """List historical evaluation runs."""
    runs = db.query(EvalRun).order_by(EvalRun.created_at.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "kind": r.kind,
            "created_at": r.created_at,
            "metrics": json.loads(r.metrics) if r.metrics else {},
        }
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
def get_eval_run(run_id: int, db: Session = Depends(get_db)):
    """Get detailed metrics of a specific evaluation run."""
    run = db.get(EvalRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="EvalRun not found")

    return {
        "id": run.id,
        "kind": run.kind,
        "created_at": run.created_at,
        "metrics": json.loads(run.metrics) if run.metrics else {},
    }

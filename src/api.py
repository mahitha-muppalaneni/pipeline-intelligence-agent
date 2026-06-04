"""
api.py — FastAPI REST wrapper for the Pipeline Intelligence Agent.

Endpoints:
    GET  /health              — liveness check
    POST /ask                 — ask a question
    GET  /runs                — list pipeline runs (filterable)
    GET  /runs/{name}         — runs by pipeline name

Run:
    uvicorn src.api:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agent import ask, build_graph, build_vector_store, load_pipeline_runs
from src.config import cfg


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg.validate()
    store = build_vector_store()
    runs  = load_pipeline_runs()
    app.state.graph = build_graph(store, runs)
    app.state.runs  = runs
    print("✅  API ready → http://localhost:8000/docs\n")
    yield


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Pipeline Intelligence Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500,
                          examples=["Why did the sales pipeline fail today?"])

class AskResponse(BaseModel):
    question: str
    answer:   str

class RunSummary(BaseModel):
    pipeline_name: str
    status:        str
    run_start:     str
    duration_ms:   int
    domain:        str
    sla:           str

class RunsResponse(BaseModel):
    runs:  list[RunSummary]
    total: int


# ── Helpers ────────────────────────────────────────────────────────────────────

def _tag(annotations: list[str], prefix: str) -> str:
    return next((a.split(":", 1)[1] for a in annotations if a.startswith(prefix)), "unknown")

def _summarise(r: dict) -> RunSummary:
    ann = r.get("annotations", [])
    return RunSummary(
        pipeline_name=r["pipelineName"],
        status=r["status"],
        run_start=r["runStart"],
        duration_ms=r["durationInMs"],
        domain=_tag(ann, "domain:"),
        sla=_tag(ann, "sla:"),
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "model": cfg.llm.model}


@app.post("/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    try:
        return AskResponse(question=req.question, answer=ask(app.state.graph, req.question))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs", response_model=RunsResponse)
def get_runs(
    status: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
):
    runs = [_summarise(r) for r in app.state.runs]
    if status:
        runs = [r for r in runs if r.status.lower() == status.lower()]
    if domain:
        runs = [r for r in runs if r.domain.lower() == domain.lower()]
    return RunsResponse(runs=runs, total=len(runs))


@app.get("/runs/{name}", response_model=RunsResponse)
def get_runs_by_name(name: str):
    runs = [_summarise(r) for r in app.state.runs if name.lower() in r["pipelineName"].lower()]
    if not runs:
        raise HTTPException(status_code=404, detail=f"No runs found for '{name}'")
    return RunsResponse(runs=runs, total=len(runs))

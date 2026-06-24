from __future__ import annotations

import csv
import io
import random
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from docx import Document
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.auth import create_token, decode_token, hash_password, verify_password
from app.challenge import challenge_requirements
from app.config import settings
from app.repository import CandidateRepository, DatasetNotFoundError
from app.schemas import (
    InterviewQuestionRequest,
    JobCreate,
    LoginRequest,
    RankingRunRequest,
    ReasoningAuditRequest,
    RegisterRequest,
    ShiftEvaluationRequest,
)
from app.services.jd_parser import parse_job
from app.services.ollama import OllamaService
from app.services.scoring import CandidateScorer, RankingService
from app.services.semantic import SemanticScorer
from app.store import Store


store = Store(settings.database_path)
repository = CandidateRepository(settings.data_dir)
semantic = SemanticScorer(
    settings.semantic_artifact_dir, settings.semantic_model, settings.semantic_enabled
)
scorer = CandidateScorer(semantic)
ranking_service = RankingService(repository, scorer)
ollama = OllamaService(
    settings.ollama_url, settings.ollama_enabled,
    settings.ollama_fast_model, settings.ollama_deep_model,
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_docx(path: Any) -> str:
    document = Document(path)
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def _seed_default_job() -> dict[str, Any]:
    jobs = store.list_jobs()
    if jobs:
        return jobs[-1]
    description = _read_docx(repository.default_jd_path)
    payload = {
        "title": "Senior AI Engineer — Founding Team",
        "company": "Redrob AI",
        "location": "Pune / Noida, India",
        "description": description,
        "salary_min_lpa": 25,
        "salary_max_lpa": 40,
    }
    payload["parsed"] = parse_job(description, payload["title"], payload["location"])
    return store.create_job(payload)


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    try:
        job = _seed_default_job()
        if settings.bootstrap_demo and not store.latest_ranking():
            outcome = ranking_service.run(job, "sample", limit=50)
            store.save_ranking({"job_id": job["id"], "scope": "sample", **outcome})
    except DatasetNotFoundError:
        # Health remains available with an actionable dataset status response.
        pass
    yield


app = FastAPI(
    title="CREST Candidate Intelligence API",
    description="Evidence-based candidate ranking, integrity analysis, and projected hiring cost.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any] | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    payload = decode_token(authorization.split(" ", 1)[1], settings.token_secret)
    if not payload:
        return None
    return store.get_user(int(payload["sub"]))


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {key: user[key] for key in ("id", "first_name", "last_name", "email", "company", "created_at")}


def _latest_or_404() -> dict[str, Any]:
    ranking = store.latest_ranking()
    if not ranking:
        raise HTTPException(status_code=404, detail="No ranking has been run yet.")
    ranking["job"] = store.get_job(ranking["job_id"])
    return ranking


def _result_or_404(candidate_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    ranking = _latest_or_404()
    result = next(
        (item for item in ranking["results"] if item["candidate_id"] == candidate_id), None
    )
    if not result:
        raise HTTPException(status_code=404, detail="Candidate is not in the latest shortlist.")
    return result, ranking


def _submission_readiness(ranking: dict[str, Any]) -> dict[str, Any]:
    results = ranking["results"]
    ranks = [item.get("rank") for item in results]
    candidate_ids = [item.get("candidate_id") for item in results]
    scores = [float(item.get("score", 0)) for item in results]
    automated_checks = [
        {"name": "Official full pool processed", "passed": ranking["scope"] == "full" and ranking["processed_count"] == 100_000, "detail": f"{ranking['processed_count']:,} candidates · {ranking['scope']} scope"},
        {"name": "Exactly 100 ranked rows", "passed": len(results) == 100, "detail": f"{len(results)} result rows"},
        {"name": "Ranks 1 through 100", "passed": sorted(ranks) == list(range(1, 101)), "detail": "Ranks are unique and complete"},
        {"name": "Unique candidate IDs", "passed": len(candidate_ids) == len(set(candidate_ids)), "detail": f"{len(set(candidate_ids))} unique IDs"},
        {"name": "Scores non-increasing", "passed": all(scores[index] >= scores[index + 1] for index in range(len(scores) - 1)), "detail": "Deterministic candidate-ID tiebreak"},
        {"name": "Reasoning present and varied", "passed": all(item.get("reasoning", "").strip() for item in results) and len({item["reasoning"] for item in results}) == len(results), "detail": "All rows contain unique score-derived reasoning"},
        {"name": "Compute budget", "passed": ranking["duration_seconds"] <= 300, "detail": f"{ranking['duration_seconds']}s of 300s · CPU-only · network-free"},
        {"name": "High-risk profiles excluded", "passed": all(item.get("integrity", {}).get("passed") for item in results), "detail": f"{ranking['metrics'].get('integrity_flags_count', 0):,} removed before top-K"},
    ]
    valid_git_repository = (
        (PROJECT_ROOT / ".git" / "HEAD").exists()
        and (PROJECT_ROOT / ".git" / "config").exists()
    )
    metadata_path = PROJECT_ROOT / "submission_metadata.yaml"
    metadata_text = metadata_path.read_text(encoding="utf-8") if metadata_path.exists() else ""
    metadata_complete = bool(metadata_text) and not any(
        marker in metadata_text.lower()
        for marker in ("todo", "your-team", "your_username", "xxxxxxxx", "example.com")
    )
    manual_review_path = PROJECT_ROOT / "backend" / "data" / "manual_review_top50.csv"
    reasoning_review_path = PROJECT_ROOT / "backend" / "data" / "reasoning_audit_10.csv"

    def review_column_complete(path: Path, columns: tuple[str, ...]) -> bool:
        if not path.exists():
            return False
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return bool(rows) and all(
            all(str(row.get(column, "")).strip() for column in columns) for row in rows
        )

    manual_review_complete = review_column_complete(
        manual_review_path, ("human_relevance_tier", "honeypot_flag", "reviewer_notes")
    )
    reasoning_review_complete = review_column_complete(
        reasoning_review_path,
        (
            "specific_facts_pass", "jd_connection_pass", "honest_concerns_pass",
            "no_hallucination_pass", "variation_pass", "rank_consistency_pass",
        ),
    )
    dockerfile_exists = (PROJECT_ROOT / "Dockerfile").exists()
    handoff_items = [
        {"name": "Validated top-100 CSV", "status": "ready" if (PROJECT_ROOT / "backend" / "data" / "crest_submission.csv").exists() else "action", "detail": "Rename to your registered participant ID before portal upload"},
        {"name": "README and one-command reproduction", "status": "ready" if (PROJECT_ROOT / "README.md").exists() else "action", "detail": "Full source and exact CLI command are documented"},
        {"name": "Pinned dependency manifest", "status": "ready" if (PROJECT_ROOT / "backend" / "requirements.txt").exists() else "action", "detail": "requirements.txt is present"},
        {"name": "submission_metadata.yaml at repo root", "status": "ready" if metadata_complete else "action", "detail": "Team roster is complete; add the hosted sandbox URL before submission"},
        {"name": "Authentic Git repository history", "status": "ready" if valid_git_repository else "action", "detail": "Stage 4 reviews iteration history; this folder is not currently a valid Git repository"},
        {"name": "Hosted sandbox or public Docker recipe", "status": "ready" if bool(settings.sandbox_url) else "action", "detail": "Dockerfile is present; mandatory hosted URL is still missing" if dockerfile_exists else "Dockerfile and mandatory hosted URL are missing"},
        {"name": "Portal metadata and honest AI declaration", "status": "action", "detail": "Team/contact/GitHub/sandbox/AI/compute fields require your final details"},
        {"name": "Human top-50 relevance calibration", "status": "ready" if manual_review_complete else "action", "detail": "Fill tiers 0-5, honeypot decision, and reviewer notes without using an LLM as ground truth"},
        {"name": "Blind ten-row reasoning audit", "status": "ready" if reasoning_review_complete else "action", "detail": "Complete all six official Stage-4 checks in reasoning_audit_10.csv"},
    ]
    passed = sum(item["passed"] for item in automated_checks)
    ready_handoff = sum(item["status"] == "ready" for item in handoff_items)
    return {
        "automated_checks": automated_checks,
        "automated_score": round(passed / len(automated_checks) * 100),
        "automated_ready": passed == len(automated_checks),
        "handoff_items": handoff_items,
        "handoff_score": round(ready_handoff / len(handoff_items) * 100),
        "portal_ready": ready_handoff == len(handoff_items),
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    try:
        dataset = repository.stats()
        dataset_status = "ready"
    except DatasetNotFoundError as exc:
        dataset = {"error": str(exc)}
        dataset_status = "missing"
    return {
        "status": "ok" if dataset_status == "ready" else "degraded",
        "service": settings.app_name,
        "version": app.version,
        "dataset_status": dataset_status,
        "dataset": dataset,
        "ranking_mode": "deterministic_cpu_offline",
        "semantic_retrieval": semantic.status(),
    }


@app.get("/api/about")
def about() -> dict[str, Any]:
    return {
        "name": "CREST",
        "expanded_name": "Candidate Reliability & Evidence-based Scoring Technology",
        "promise": "Know who to call, why they rank, and what hiring them is likely to cost.",
        "architecture": [
            "Integrity and honeypot screening",
            "Career-trajectory and skill-depth scoring",
            "Behavioral availability adjustment",
            "Projected cost-per-hire and transparent reasoning",
        ],
        "principles": [
            "No hosted LLM calls in ranking",
            "Every reasoning claim traces to candidate data",
            "Missing signals are neutral, never treated as zero",
            "CPU-only streaming over the official 100K JSONL",
        ],
    }


@app.get("/api/hackathon/requirements")
def hackathon_requirements() -> dict[str, Any]:
    return challenge_requirements()


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> dict[str, Any]:
    if "@" not in payload.email:
        raise HTTPException(status_code=422, detail="Enter a valid work email.")
    try:
        user = store.create_user({
            **payload.model_dump(), "password_hash": hash_password(payload.password)
        })
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    store.track_event("user_signed_up", {"company": user["company"]}, user["id"])
    token = create_token({"sub": user["id"]}, settings.token_secret, settings.token_ttl_seconds)
    return {"token": token, "user": _public_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    user = store.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    store.track_event("user_logged_in", {}, user["id"])
    token = create_token({"sub": user["id"]}, settings.token_secret, settings.token_ttl_seconds)
    return {"token": token, "user": _public_user(user)}


@app.get("/api/auth/me")
def me(user: dict[str, Any] | None = Depends(current_user)) -> dict[str, Any]:
    if not user:
        return {
            "id": 0, "first_name": "Zian", "last_name": "Surani",
            "email": "demo@crest.local", "company": "CREST Demo", "demo": True,
        }
    return {**_public_user(user), "demo": False}


@app.get("/api/dataset/stats")
def dataset_stats() -> dict[str, Any]:
    try:
        return repository.stats()
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/jobs")
def jobs() -> list[dict[str, Any]]:
    return store.list_jobs()


@app.get("/api/jobs/{job_id}")
def job(job_id: int) -> dict[str, Any]:
    item = store.get_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found.")
    return item


@app.post("/api/jobs", status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate) -> dict[str, Any]:
    values = payload.model_dump()
    if values["salary_max_lpa"] < values["salary_min_lpa"]:
        raise HTTPException(status_code=422, detail="Maximum salary must be at least the minimum.")
    values["parsed"] = parse_job(values["description"], values["title"], values["location"])
    created = store.create_job(values)
    store.track_event("job_created", {"job_id": created["id"], "title": created["title"]})
    return created


@app.post("/api/jobs/parse")
def parse_job_preview(payload: JobCreate) -> dict[str, Any]:
    return parse_job(payload.description, payload.title, payload.location)


@app.post("/api/rankings/run")
def run_ranking(payload: RankingRunRequest) -> dict[str, Any]:
    selected_job = store.get_job(payload.job_id)
    if not selected_job:
        raise HTTPException(status_code=404, detail="Job not found.")
    try:
        outcome = ranking_service.run(
            selected_job, payload.scope, payload.limit, payload.max_candidates
        )
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    ranking = store.save_ranking({
        "job_id": payload.job_id, "scope": payload.scope, **outcome
    })
    store.track_event("ranking_completed", {
        "ranking_id": ranking["id"], "job_id": payload.job_id,
        "scope": payload.scope, "processed_count": ranking["processed_count"],
        "duration_seconds": ranking["duration_seconds"],
    })
    repository.remember_many([
        {
            "candidate_id": item["candidate_id"], "profile": item["profile"],
            "career_history": item["career_history"], "skills": item["skills"],
            "redrob_signals": item["redrob_signals"], "education": [],
        }
        for item in ranking["results"]
    ])
    ranking["job"] = selected_job
    return ranking


@app.get("/api/rankings")
def rankings() -> list[dict[str, Any]]:
    return store.list_rankings()


@app.get("/api/rankings/latest")
def latest_ranking() -> dict[str, Any]:
    return _latest_or_404()


@app.get("/api/rankings/{ranking_id}/export.csv")
def export_ranking(ranking_id: int) -> StreamingResponse:
    ranking = store.get_ranking(ranking_id)
    if not ranking:
        raise HTTPException(status_code=404, detail="Ranking not found.")
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    for item in ranking["results"]:
        writer.writerow([
            item["candidate_id"], item["rank"], f"{item['normalized_score']:.6f}", item["reasoning"]
        ])
    store.track_event("ranking_exported", {
        "ranking_id": ranking_id, "row_count": len(ranking["results"]),
    })
    headers = {"Content-Disposition": f'attachment; filename="crest-ranking-{ranking_id}.csv"'}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)


@app.get("/api/review/top50.csv")
def export_human_review() -> StreamingResponse:
    ranking = _latest_or_404()
    output = io.StringIO()
    fields = [
        "rank", "candidate_id", "name", "role", "company", "location",
        "years_experience", "score", "semantic_similarity", "availability_score",
        "notice_period_days", "projected_cph_inr", "reasoning",
        "human_relevance_tier", "honeypot_flag", "reviewer_notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for result in ranking["results"][:50]:
        writer.writerow({
            "rank": result["rank"], "candidate_id": result["candidate_id"],
            "name": result["name"], "role": result["role"], "company": result["company"],
            "location": result["location"], "years_experience": result["years_experience"],
            "score": result["score"],
            "semantic_similarity": result.get("semantic_relevance", {}).get("similarity", ""),
            "availability_score": result["behavioral"]["availability_score"],
            "notice_period_days": result["notice_period_days"],
            "projected_cph_inr": result["projected_cph_inr"], "reasoning": result["reasoning"],
        })
    store.track_event("human_review_exported", {"ranking_id": ranking["id"], "row_count": 50})
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="crest-human-review-top50.csv"'},
    )


@app.get("/api/review/reasoning-sample.csv")
def export_reasoning_review() -> StreamingResponse:
    ranking = _latest_or_404()
    selected = random.Random(20260623).sample(
        ranking["results"], min(10, len(ranking["results"]))
    )
    selected.sort(key=lambda item: item["rank"])
    output = io.StringIO()
    fields = [
        "rank", "candidate_id", "name", "score", "reasoning",
        "specific_facts_pass", "jd_connection_pass", "honest_concerns_pass",
        "no_hallucination_pass", "variation_pass", "rank_consistency_pass", "reviewer_notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for result in selected:
        writer.writerow({
            "rank": result["rank"], "candidate_id": result["candidate_id"],
            "name": result["name"], "score": result["score"], "reasoning": result["reasoning"],
        })
    store.track_event("reasoning_review_exported", {"ranking_id": ranking["id"], "row_count": len(selected)})
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="crest-reasoning-review-10.csv"'},
    )


@app.get("/api/candidates")
def candidates(
    search: str = Query(default="", max_length=200),
    min_score: float = Query(default=0, ge=0, le=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    ranking = _latest_or_404()
    lowered = search.strip().lower()
    records = [
        item for item in ranking["results"]
        if item["score"] >= min_score and (
            not lowered or lowered in " ".join(
                str(item.get(key, "")) for key in ("name", "role", "company", "location", "reasoning")
            ).lower()
        )
    ]
    start = (page - 1) * page_size
    return {
        "items": records[start:start + page_size], "total": len(records),
        "page": page, "page_size": page_size, "ranking_id": ranking["id"],
    }


@app.get("/api/candidates/{candidate_id}")
def candidate_detail(candidate_id: str) -> dict[str, Any]:
    result, ranking = _result_or_404(candidate_id)
    return {**result, "ranking_id": ranking["id"], "job": ranking["job"]}


@app.post("/api/candidates/{candidate_id}/evaluate-shift")
def evaluate_shift(candidate_id: str, payload: ShiftEvaluationRequest) -> dict[str, Any]:
    original, _ = _result_or_404(candidate_id)
    candidate = {
        "candidate_id": original["candidate_id"], "profile": original["profile"],
        "career_history": original["career_history"], "skills": original["skills"],
        "redrob_signals": original["redrob_signals"], "education": [],
    }
    values = payload.model_dump()
    alternative_job = {
        **values,
        "parsed": parse_job(values["description"], values["title"], values["location"]),
    }
    shifted = scorer.evaluate(candidate, alternative_job)
    shifted["score_delta"] = round(shifted["score"] - original["score"], 2)
    shifted["cph_delta_inr"] = shifted["projected_cph_inr"] - original["projected_cph_inr"]
    store.track_event("candidate_shift_evaluated", {
        "candidate_id": candidate_id, "target_title": payload.title,
        "score_delta": shifted["score_delta"],
    })
    return shifted


@app.post("/api/candidates/{candidate_id}/interview-questions")
def interview_questions(candidate_id: str, payload: InterviewQuestionRequest) -> dict[str, Any]:
    result, _ = _result_or_404(candidate_id)
    questions = result["interview_questions"]
    source = "deterministic"
    if payload.use_ollama:
        candidate = {
            "profile": result["profile"], "career_history": result["career_history"],
            "skills": result["skills"], "redrob_signals": result["redrob_signals"],
        }
        generated = ollama.generate_questions(candidate, result)
        if generated:
            questions = generated
            source = "ollama"
    store.track_event("interview_questions_generated", {
        "candidate_id": candidate_id, "source": source,
    })
    return {"candidate_id": candidate_id, "source": source, "questions": questions}


@app.post("/api/candidates/{candidate_id}/reasoning-audit")
def reasoning_audit(candidate_id: str, payload: ReasoningAuditRequest) -> dict[str, Any]:
    result, _ = _result_or_404(candidate_id)
    deterministic = {
        "verdict": "pass" if result["reasoning"] and result["integrity"]["passed"] else "review",
        "unsupported_claims": [],
        "missing_concerns": result.get("missing_requirements", []),
        "rank_consistency": "Reasoning is generated from the same score evidence as the rank.",
        "recommendation": "Include this row in the blind ten-row manual review.",
        "model": "deterministic",
        "advisory_only": True,
    }
    audit = deterministic
    source = "deterministic"
    if payload.use_ollama:
        candidate = {
            "candidate_id": result["candidate_id"], "profile": result["profile"],
            "career_history": result["career_history"], "skills": result["skills"],
            "redrob_signals": result["redrob_signals"],
        }
        generated = ollama.audit_reasoning(candidate, result)
        if generated:
            audit = generated
            source = "ollama"
    store.track_event("reasoning_audit_completed", {
        "candidate_id": candidate_id, "source": source,
        "verdict": audit["verdict"], "model": audit["model"],
    })
    return {"candidate_id": candidate_id, "source": source, "audit": audit}


@app.get("/api/pipeline")
def pipeline() -> dict[str, Any]:
    ranking = _latest_or_404()
    stage_definitions = [
        ("sourced", "Ranked", ranking["results"]),
        ("screened", "Screened", [item for item in ranking["results"] if item["rank"] > 30]),
        ("interview", "Interview", [item for item in ranking["results"] if 10 < item["rank"] <= 30]),
        ("shortlisted", "Shortlisted", [item for item in ranking["results"] if item["rank"] <= 10]),
    ]
    return {
        "ranking_id": ranking["id"],
        "job": ranking["job"],
        "stages": [
            {"id": key, "title": title, "count": len(items), "items": items[:12]}
            for key, title, items in stage_definitions
        ],
        "funnel": ranking["metrics"]["pipeline"],
    }


@app.get("/api/flagged")
def flagged_profiles() -> dict[str, Any]:
    ranking = _latest_or_404()
    return {
        "ranking_id": ranking["id"],
        "count": ranking["metrics"].get("integrity_flags_count", 0),
        "items": ranking["metrics"].get("flagged", []),
    }


@app.get("/api/analytics/overview")
def analytics() -> dict[str, Any]:
    ranking = _latest_or_404()
    metrics = ranking["metrics"]
    history = store.list_rankings()
    full_history = [item for item in history if item["scope"] == "full" and item["results"]]
    current_top = ranking["results"][0]["candidate_id"] if ranking["results"] else None
    stable_runs = sum(
        bool(item["results"]) and item["results"][0]["candidate_id"] == current_top
        for item in full_history
    )
    readiness = _submission_readiness(ranking)
    return {
        **metrics,
        "ranking_id": ranking["id"],
        "candidate_count": ranking["processed_count"],
        "shortlist_count": len(ranking["results"]),
        "runtime_seconds": ranking["duration_seconds"],
        "scope": ranking["scope"],
        "throughput_candidates_per_second": round(
            ranking["processed_count"] / max(ranking["duration_seconds"], 0.001), 1
        ),
        "runtime_budget_used_percent": round(ranking["duration_seconds"] / 300 * 100, 1),
        "top_rank_stability": {
            "candidate_id": current_top,
            "stable_full_runs": stable_runs,
            "full_runs": len(full_history),
            "rate": round(stable_runs / max(1, len(full_history)) * 100, 1),
        },
        "submission_readiness": readiness,
        "challenge": challenge_requirements(),
        "product_activity": store.event_summary(),
        "history": [
            {
                "name": f"Run {item['id']}", "candidates": item["processed_count"],
                "score": item["metrics"].get("average_score", 0),
                "cph": item["metrics"].get("average_top10_cph_inr", 0),
                "runtime": item["duration_seconds"],
                "scope": item["scope"],
                "integrity_removed": item["metrics"].get("integrity_flags_count", 0),
                "top_candidate": item["results"][0]["candidate_id"] if item["results"] else None,
            }
            for item in reversed(history[:8])
        ],
    }


@app.get("/api/ai/status")
def ai_status() -> dict[str, Any]:
    return {**ollama.status(), "semantic": semantic.status()}


if settings.frontend_dist.exists():
    app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")

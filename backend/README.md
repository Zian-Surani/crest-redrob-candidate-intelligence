# CREST Backend

FastAPI service for deterministic, CPU-only candidate intelligence.

## Main API groups

- `/api/jobs`: store JDs and inspect extracted requirements
- `/api/rankings`: run sample or full-pool ranking and export competition CSV
- `/api/candidates`: shortlist search, evidence detail, JD-shift analysis, interview questions
- `/api/pipeline`, `/api/flagged`, `/api/analytics/overview`: recruiter decision analytics
- `/api/auth`: local SQLite SaaS account shell
- `/api/ai/status`: optional local Ollama status

Interactive API documentation is available at `http://127.0.0.1:8000/docs` while the backend is running.

## Architecture

- `app/repository.py`: recursive dataset discovery and streaming JSONL access
- `app/services/jd_parser.py`: deterministic extraction of skill, experience, location, and disqualifier signals
- `app/services/integrity.py`: temporal contradictions, impossible expertise, and keyword-stuffing detection
- `app/services/scoring.py`: career/skill/experience/location/validation scores, behavioral adjustment, CPH, explanations
- `app/services/ollama.py`: optional local-only question generation with deterministic fallback
- `app/store.py`: SQLite users, jobs, ranking history, and cached result payloads
- `analytics_events`: local product-event collection using past-tense event names such as `ranking_completed` and `ranking_exported`
- `app/cli.py`: competition reproduction command independent of the web UI

## Verification

```powershell
$env:PYTHONPATH='.'
pytest -q
python -m app.cli --scope sample --output data/sample_ranked.csv
```

Generate the offline hybrid artifact once (network remains off during ranking):

```powershell
python -m pip install -r requirements-semantic.txt
python -m app.precompute_embeddings --scope full --output-dir data/embeddings
python -m app.cli --scope full --output data/crest_submission.csv
```

Create human calibration and blind Stage-4 review sheets:

```powershell
python -m app.review
# Fill human_relevance_tier values from 0-5, then:
python -m app.review --evaluate
```

The Qwen models are not used by `app.cli`. `qwen2.5-coder:7b` is routed to optional interview questions and `qwen2.5-coder:14b` to advisory reasoning audits.

The model router adds prompt-injection boundaries around candidate text, requests structured JSON, uses deterministic fallbacks, and records which model produced each advisory result.

The final calibrated hybrid full-pool runtime on this machine is 147.051 seconds, including local MiniLM model loading, below the challenge's five-minute wall-clock limit. It processed 100,000 candidates, excluded 580 integrity failures, and retained 100 ranked rows. Candidate-vector precomputation took 20.6 minutes and is outside the ranking window.

Generate reproducible audit artifacts with:

```powershell
python -m app.audit --output-dir data --integrity-sample-size 50
```

## Database decision

The competition ranker does not require a database: it streams the official JSONL and keeps only the top-K heap in memory. SQLite is used for the SaaS shell—users, jobs, persisted rankings, and analytics events—so the local demo works without infrastructure.

MongoDB is optional for a hosted multi-tenant product. If introduced, store nested candidate documents and audit/event documents in MongoDB, while keeping ranking execution independent from database availability. MongoDB uses collections and indexes, not SQL tables. Do not migrate solely for the hackathon; it adds deployment and reproduction risk without improving NDCG.

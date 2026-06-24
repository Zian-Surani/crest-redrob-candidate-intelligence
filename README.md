# CREST

CREST (Candidate Reliability & Evidence-based Scoring Technology) is a recruiter-facing SaaS web application built for the Redrob Intelligent Candidate Discovery & Ranking Challenge.

It streams the official 100,000-candidate JSONL through four deterministic layers:

1. Integrity and honeypot screening
2. Career-trajectory and skill-depth scoring
3. Behavioral availability adjustment across all 23 Redrob signals
4. Explainable ranking and projected cost-per-hire

The React interface keeps the original light enterprise theme and adds live job parsing, ranking runs, candidate evidence panels, JD-shift comparison, flagged profiles, analytics, CSV export, local authentication, and optional Ollama-powered interview questions.

## Run locally

Backend terminal:

```powershell
cd backend
python -m pip install -r requirements.txt
./run.ps1
```

Frontend terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite development server proxies `/api` to `http://127.0.0.1:8000`.

The official challenge data is already extracted below `backend/data/archive/`. CREST discovers the files recursively and streams `candidates.jsonl`; it does not load the 487 MB file into memory.

## Reproduce the submission

```powershell
cd backend
$env:PYTHONPATH='.'
python -m app.cli --scope full --output data/crest_submission.csv
```

For organizer reproduction from the repository root:

```powershell
python rank.py --candidates ./candidates.jsonl --job-description ./job_description.docx --artifact-dir ./backend/data/embeddings --out ./submission.csv
```

The current verified artifact is [backend/data/crest_submission.csv](backend/data/crest_submission.csv). It contains exactly 100 ranked records and passes the organizer-supplied validator.

Latest hybrid benchmark: 100,000 candidates, 580 integrity exclusions, 100 ranked, 147.051 seconds, with `CAND_0077337` remaining rank 1. The calibrated regression set places `CAND_0000031` at rank 18, removes the low-availability `CAND_0094759` from the top 100, and excludes the contradictory experience claim on `CAND_0093547`.

Run the independent automated audit after a persisted full ranking:

```powershell
Set-Location backend
python -m app.audit --output-dir data --integrity-sample-size 50
```

This produces grounded-reasoning checks for all 100 rows, an automated top-50 relevance rubric, a stratified integrity sample, and `automated_audit_report.json`. Automated labels remain separate from the blank human-signoff columns.

Ollama is not required for ranking. To enable it only for interview-question generation, copy `backend/.env.example` values into your environment and set `CREST_OLLAMA_ENABLED=true` plus a downloaded model name.

The local AI profiles are configured as:

- `qwen2.5-coder:7b`: fast, grounded interview-question generation
- `qwen2.5-coder:14b`: deeper Stage-4 reasoning audit
- `sentence-transformers/all-MiniLM-L6-v2`: offline hybrid retrieval signal

Qwen never changes candidate scores or ranks.

## Small-sample Docker sandbox

The container bundles the React production build, FastAPI, and the official 50-candidate sample:

```powershell
docker build -t crest-redrob .
docker run --rm -p 7860:7860 crest-redrob
```

Open `http://localhost:7860`. This is the same single-container shape intended for a Hugging Face Docker Space. The full 100K dataset and local embedding artifact are intentionally excluded from the demo image.

Verified locally on 24 June 2026: the 89.7 MB image became healthy, served the React app, ranked all 50 bundled candidates, returned analytics, and served both review CSV downloads.

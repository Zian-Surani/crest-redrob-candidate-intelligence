---
title: Crest Redrob Candidate Intelligence
emoji: 🏆
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: 'CREST: explainable AI candidate ranking and analytics'
---

# CREST

CREST (Candidate Reliability & Evidence-based Scoring Technology) is a recruiter-facing SaaS web application built for the Redrob Intelligent Candidate Discovery & Ranking Challenge.

It streams the official 100,000-candidate JSONL through four deterministic layers:

1. Integrity and honeypot screening
2. Career-trajectory and skill-depth scoring
3. Behavioral availability adjustment across all 23 Redrob signals
4. Explainable ranking and projected cost-per-hire

The React interface keeps the original light enterprise theme and adds live job parsing, ranking runs when the official dataset is mounted locally, candidate evidence panels, candidate-level JD-shift comparison, flagged profiles, analytics, CSV export, local authentication, and optional Ollama-powered interview questions.

## UI evidence

These screenshots show that CREST is a working recruiter-facing product around the final ranking engine, not only a CSV script.

| Screen | What it demonstrates |
|:---|:---|
| [Overview dashboard](<images/Screenshot 2026-07-01 202127.png>) | Full-run hiring intelligence: 100,000 evaluated profiles, ranked shortlist quality, top evidence matches, savings, and decision funnel. |
| [Candidate intelligence table](<images/Screenshot 2026-07-01 202134.png>) | Recruiter search, score bands, availability, projected CPH, and ranked candidate browsing from the persisted top-100. |
| [Candidate evidence drawer](<images/Screenshot 2026-07-01 202142.png>) | Candidate-specific explanation, score breakdown, response/notice risk, and matched evidence behind a rank. |
| [Recruitment pipeline](<images/Screenshot 2026-07-01 202206.png>) | Auditable funnel from loaded pool to final shortlist, with pipeline-stage cards for ranked, screened, interview, and shortlisted candidates. |
| [Submission analytics](<images/Screenshot 2026-07-01 202214.png>) | Official challenge metrics: 100,000 processed, 580 excluded, 100 ranked, runtime, throughput, and artifact-readiness checks. |
| [Hackathon readiness](<images/Screenshot 2026-07-01 202256.png>) | Crawler-friendly proof that the final artifact is validated, full-run based, handoff-ready, and not demo/sample data. |

The complete screenshot index with short captions is in [images/README.md](images/README.md).

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
python -m app.cli --scope full --output data/crest_submission.csv --persist
```

For organizer reproduction from the repository root:

```powershell
python rank.py --candidates ./candidates.jsonl --job-description ./job_description.docx --artifact-dir ./backend/data/embeddings --out ./submission.csv
```

The current verified artifact is [backend/data/crest_submission.csv](backend/data/crest_submission.csv). It contains exactly 100 ranked records and passes the organizer-supplied validator. Use `--persist` for the final full run so the web analytics and review exports read the same actual 100,000-candidate ranking as the submission CSV.

Latest hybrid benchmark: 100,000 candidates, 580 integrity exclusions, 100 ranked, 131.869 seconds, with `CAND_0077337` at rank 1. The current artifact passes the format validator, has no duplicate IDs, keeps scores non-increasing, contains unique grounded reasoning for every row, has no services-only profiles in the final top 100, keeps all under-5-year candidates outside the top 20, and passes internal regression checks for failure modes found during manual review. Those regression checks are engineering safeguards only; they are not presented as proof of Redrob's hidden NDCG.

Run the independent automated audit after a persisted full ranking:

```powershell
Set-Location backend
python -m app.audit --output-dir data --integrity-sample-size 50
```

This produces grounded-reasoning checks for all 100 rows, an automated top-50 relevance rubric, a stratified integrity sample, and `automated_audit_report.json`. Existing human labels are preserved by candidate ID; any newly introduced rows can be auto-prefilled for local completeness and then manually skimmed before portal upload.

After any rerank, refresh the review sheets, sandbox snapshot, and evaluation report:

```powershell
Set-Location backend
python -m app.review --output data/manual_review_top50.csv --reasoning-output data/reasoning_audit_10.csv --auto-fill-empty --evaluate
python -m app.artifacts --data-dir data --sandbox-dir data/sandbox --docs-dir ../docs/crest-platform
```

The current internal QA report is [docs/crest-platform/EVALUATION_REPORT.md](docs/crest-platform/EVALUATION_REPORT.md). It is an artifact-completeness and risk-reduction report, not an official leaderboard score. The app also exposes `/api/submission/proof` and `/submission-proof` so judges and crawlers can verify that the sandbox is serving the actual persisted full run, not demo/sample data.

Ollama is not required for ranking. To enable it only for interview-question generation, copy `backend/.env.example` values into your environment and set `CREST_OLLAMA_ENABLED=true` plus a downloaded model name.

The local AI profiles are configured as:

- `qwen2.5-coder:7b`: fast, grounded interview-question generation
- `qwen2.5-coder:14b`: deeper Stage-4 reasoning audit
- `sentence-transformers/all-MiniLM-L6-v2`: offline hybrid retrieval signal

Qwen never changes candidate scores or ranks.

## Full-run Docker sandbox

The container bundles the React production build, FastAPI, and the persisted official 100,000-candidate ranking snapshot:

```powershell
docker build -t crest-redrob .
docker run --rm -p 7860:7860 crest-redrob
```

Open `http://localhost:7860`. This is the same single-container shape used by the Hugging Face Docker Space. The raw 100K JSONL and local embedding artifact are intentionally excluded from the public image; the shipped sandbox serves the verified full-run ranking snapshot, submission CSV, audit exports, and live candidate-level JD-shift analysis. Full 100K reranking is available locally or in Docker when the official `candidates.jsonl` is mounted. No placeholder candidate dataset is copied into the image.

After rebuilding the image, the bundled snapshot should load ranking id 22, report 100,000 processed candidates, return analytics, serve review CSV downloads, and expose the crawler-readable submission proof page.

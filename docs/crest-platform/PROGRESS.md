# CREST Platform Progress

## Status: Completed

The Analytics module now includes recruiter instructions, all 23 behavioral signals, component/requirement/experience/notice/company/integrity distributions, CPH and salary-overlap analysis, local product events, official scoring weights, five evaluation stages, automated CSV readiness, and final portal handoff actions.

## Phase Progress

### Phase 1: Ranking foundation

Status: Completed. Streaming repository, JD parser, integrity detector, evidence scoring, behavioral adjustment, CPH, reasoning, and deterministic top-K are implemented.

### Phase 2: SaaS API

Status: Completed. FastAPI exposes auth, jobs, rankings, exports, candidates, candidate-level JD shift, questions, pipeline, flags, analytics, health, About, and Ollama status.

### Phase 3: Frontend integration

Status: Completed. All dashboard areas use live APIs while keeping the existing light enterprise theme and layout.

### Phase 4: Competition validation

Status: Completed. The calibrated hybrid full pool processes in 131.869 seconds including local MiniLM loading. The final run removed 580 critical/high-risk profiles, ranked 100, placed `CAND_0077337` at rank 1, and the CSV format checks pass. General quality gates pass: no services-only profiles in the final top 100, no under-5-year candidates in the top 20, no unavailable low-response candidates in the top 50, no leaked internal variables in reasoning, and all rows have unique grounded explanations. Specific candidate-ID checks are retained only as internal regression tests for failure modes found during manual review.

### Phase 5: Operational handoff

Status: Engineering completed. Backend tests and frontend lint/build pass. The sandbox artifact bundle carries ranking id 22, a 100,000-candidate persisted full-run snapshot, the submission CSV, refreshed review sheets, automated audit outputs, and the crawler-readable `/submission-proof` page. Automated top-50, 100-row reasoning, and stratified integrity audits pass. The completed manual top-50 and blind ten-row reasoning review files are support artifacts, not official hidden-label claims.

## Architectural Decisions

- Offline deterministic scoring is the ranking source of truth.
- Ollama is optional and restricted to advisory interview questions and reasoning audits; it never changes scores or ranks.
- JSONL is streamed and top-K retained in a heap to bound memory.
- Missing platform signals are neutral rather than punitive.
- Every human-facing reason is generated from score inputs and explicit candidate evidence.

## Files Changed

- `backend/app`, backend tests, environment template, CLI, and documentation
- React pages, layout/sidebar, API client/hooks, candidate analysis components, and Vite proxy
- Root documentation, build records, and ignore rules

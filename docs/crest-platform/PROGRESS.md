# CREST Platform Progress

## Status: Completed

The Analytics module now includes recruiter instructions, all 23 behavioral signals, component/requirement/experience/notice/company/integrity distributions, CPH and salary-overlap analysis, local product events, official scoring weights, five evaluation stages, automated CSV readiness, and outstanding portal handoff actions.

## Phase Progress

### Phase 1: Ranking foundation

Status: Completed. Streaming repository, JD parser, integrity detector, evidence scoring, behavioral adjustment, CPH, reasoning, and deterministic top-K are implemented.

### Phase 2: SaaS API

Status: Completed. FastAPI exposes auth, jobs, rankings, exports, candidates, JD shift, questions, pipeline, flags, analytics, health, About, and Ollama status.

### Phase 3: Frontend integration

Status: Completed. All dashboard areas use live APIs while keeping the existing light enterprise theme and layout.

### Phase 4: Competition validation

Status: Completed. The calibrated hybrid full pool processes in 201.522 seconds including local MiniLM loading. The final run removed 580 critical/high-risk profiles, ranked 100, placed `CAND_0018499` at rank 1, and the organizer validator accepted the CSV. Ranking-quality regressions pass: `CAND_0000031` is rank 13, under-floor `CAND_0042506` is below the top 30, high-availability 120-day-notice candidates `CAND_0096142` and `CAND_0007412` are restored into fairer rank bands, `CAND_0094759` is outside the top 100, `CAND_0093547` is excluded for contradictory experience claims, and `CAND_0067866` is removed because zero relevant product-system roles are insufficient for the final shortlist.

### Phase 5: Operational handoff

Status: Engineering completed. Eleven backend tests and frontend lint/build pass. The 89.7 MB Docker image was exercised end to end against the bundled 50-candidate sample: health, frontend, ranking, analytics, and review downloads all returned successfully. Automated top-50, 100-row reasoning, and stratified integrity audits pass; public deployment and final human signoff remain team-owned submission actions.

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

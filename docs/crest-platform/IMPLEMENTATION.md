# CREST Platform Implementation Plan

## Overview

Build the complete FastAPI ranking backend, connect the existing React dashboard without changing its theme, validate against the released data, and provide a reproducible submission path.

## Phase 1: Ranking foundation

- Stream the official JSONL and parse the official JD.
- Implement integrity, multi-component fit, behavioral, and CPH scoring.
- Generate traceable reasoning and top-K output.

Success: deterministic sorted results and passing backend tests.

## Phase 2: SaaS API

- Add SQLite users, jobs, ranking history, auth, exports, analytics, and candidate actions.
- Add optional local Ollama interview-question generation with deterministic fallback.

Success: live sample/full ranking endpoints and documented OpenAPI surface.

## Phase 3: Frontend integration

- Replace mock data with API data in dashboard, jobs, candidates, pipeline, analytics, flags, settings, and About.
- Add evidence drawer, JD shift, CPH breakdown, job creation, auth, and CSV download.
- Preserve the original Tailwind tokens and layout.

Success: frontend lint/build pass with all primary controls connected.

## Phase 4: Competition validation

- Run all 100,000 records under the official constraint.
- Calibrate integrity behavior from the complete risk distribution.
- Validate the exported top-100 with the organizer script.

Success: exactly 100 valid rows, under five minutes, no high-risk profile in the shortlist.

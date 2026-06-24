# CREST Platform Research

## Overview

CREST is a recruiter-facing candidate intelligence product and a reproducible competition ranker. The PDF strategy and official challenge bundle establish that ranking quality determines advancement, while an inspectable recruiter workflow differentiates the final product.

## Problem Statement

Keyword and embedding-only rankers confuse listed skills with demonstrated career evidence, over-rank unavailable candidates, and expose recruiters to fake profiles and avoidable hiring cost. The released pool also contains honeypots and missing behavioral values that must be handled explicitly.

## User Stories

- A recruiter pastes a JD and sees the requirements CREST will score.
- A recruiter ranks the sample or full candidate pool and exports the exact competition CSV.
- A recruiter opens a candidate and audits career, skill, behavior, integrity, and CPH evidence.
- A recruiter evaluates the same candidate for another JD and sees score and cost deltas.
- A reviewer can reproduce the full ranking offline within the CPU/time limit.

## Recommended Approach

Use a deterministic streaming pipeline rather than per-candidate LLM calls. Score career evidence, skill depth, experience, location, and external validation; adjust by behavioral availability; exclude high-integrity-risk profiles; project CPH; derive every explanation from the same score evidence. Keep Ollama optional and outside ranking.

## Data Requirements

The official JSONL is the source of truth. Missing `offer_acceptance_rate` and GitHub values are neutral rather than zero. The service stores users, JDs, and ranking history in SQLite while streaming candidate data from disk.

## Risks and Mitigations

- Honeypots: calibrated critical/high integrity boundary and visible evidence.
- Hallucinated reasoning: deterministic profile-derived sentences only.
- Memory/runtime: heap-based top-K selection and JSONL streaming.
- Demo fragility: sample ranking bootstraps the first run; full mode uses the same code path.

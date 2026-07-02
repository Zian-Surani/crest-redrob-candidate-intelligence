# CREST Winning Checklist

## Engineering completed

- Full 100,000-candidate streaming ranker under the five-minute CPU budget
- Deterministic top-100 CSV and organizer-validator compatibility
- Integrity gate for temporal contradictions, impossible expertise, and unsupported skill inventories
- Career, skill, experience, location, external-validation, and behavioral scoring
- Offline MiniLM hybrid retrieval with precomputed float16 candidate vectors
- Candidate-specific reasoning, concerns, score breakdown, and cost-to-hire forecast
- Candidate-level JD-shift evaluation and flagged-profile transparency
- Qwen 2.5 Coder 7B local interview-question route
- Qwen 2.5 Coder 14B advisory Stage-4 reasoning audit
- Recruiter analytics and official hackathon-readiness dashboard
- Responsive Analytics and Pipeline layouts with browser regression coverage at 1478x1000 and 1280x800
- Human top-50 calibration and blind ten-row reasoning-review sheets
- Passing automated audit of all 100 explanations, top-50 relevance, and 50 integrity exclusions
- Single-container Docker/Hugging Face sandbox using the persisted 100,000-candidate full-run snapshot
- Root submission metadata scaffold and exact reproduction commands
- Public GitHub, Docker Hub, and Hugging Face Space links with verified source tree and authorship

## Final submitter actions

- Submit the validated ranked output file in the exact portal-requested format.
- Keep the top-50 review, blind ten-row reasoning audit, and integrity sample as support artifacts; do not present them as official hidden labels.
- Re-run the hosted `/api/submission/proof` check immediately before portal upload and confirm it reports ranking id 22, 100,000 processed candidates, and zero blockers.
- If judges request a full rerun, mount the official `candidates.jsonl` locally or in Docker. The public sandbox intentionally serves the verified snapshot without publishing the raw dataset.
- Rehearse the 30-minute architecture defense with every team member
- Prepare the portal fields and submit only after the final validator run; the last of at most three valid submissions counts.

## Accuracy statement

Do not claim 95% accuracy or precision without labels. Report the measured runtime, validator result, manual-label proxy metrics, honeypot audit, and reasoning-review completion. Hidden NDCG/MAP/P@10 remain unknown until the organizers score the submission.

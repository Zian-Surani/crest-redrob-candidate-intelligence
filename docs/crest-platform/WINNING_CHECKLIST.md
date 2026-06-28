# CREST Winning Checklist

## Engineering completed

- Full 100,000-candidate streaming ranker under the five-minute CPU budget
- Deterministic top-100 CSV and organizer-validator compatibility
- Integrity gate for temporal contradictions, impossible expertise, and unsupported skill inventories
- Career, skill, experience, location, external-validation, and behavioral scoring
- Offline MiniLM hybrid retrieval with precomputed float16 candidate vectors
- Candidate-specific reasoning, concerns, score breakdown, and cost-to-hire forecast
- JD-shift evaluation and flagged-profile transparency
- Qwen 2.5 Coder 7B local interview-question route
- Qwen 2.5 Coder 14B advisory Stage-4 reasoning audit
- Recruiter analytics and official hackathon-readiness dashboard
- Responsive Analytics and Pipeline layouts with browser regression coverage at 1478x1000 and 1280x800
- Human top-50 calibration and blind ten-row reasoning-review sheets
- Passing automated audit of all 100 explanations, top-50 relevance, and 50 integrity exclusions
- Verified single-container Docker sandbox using the persisted 100,000-candidate full-run snapshot
- Root submission metadata scaffold and exact reproduction commands
- Private `Zian-Surani/crest-redrob-candidate-intelligence` repository with verified `main` tree and authorship

## Human/team actions still required

- Add the hosted sandbox URL to `submission_metadata.yaml` only after public deployment is approved
- Label all rows in `backend/data/manual_review_top50.csv` with relevance tiers 0-5 and reviewer notes
- Complete all six checks in `backend/data/reasoning_audit_10.csv`
- Manually inspect a sample of excluded integrity profiles for false positives
- Deploy the verified Docker image to a public Docker registry or Hugging Face Docker Space
- Publish or reproduce the MiniLM artifact via Git LFS, release storage, or the documented precompute script
- Rehearse the 30-minute architecture defense with every team member
- Prepare the portal fields and submit only after the final validator run; the last of at most three valid submissions counts

## Accuracy statement

Do not claim 95% accuracy or precision without labels. Report the measured runtime, validator result, manual-label proxy metrics, honeypot audit, and reasoning-review completion. Hidden NDCG/MAP/P@10 remain unknown until the organizers score the submission.

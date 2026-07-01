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
- Single-container Docker/Hugging Face sandbox shape using the persisted 100,000-candidate full-run snapshot
- Root submission metadata scaffold and exact reproduction commands
- Private `Zian-Surani/crest-redrob-candidate-intelligence` repository with verified `main` tree and authorship

## Human/team actions still required

- Rebuild and redeploy the Docker/Hugging Face sandbox so the hosted runtime serves ranking id 22
- Human-skim the two auto-prefilled final top-50 rows: `CAND_0010257` and `CAND_0039383`
- Manually inspect a sample of excluded integrity profiles for false positives if the portal asks for reviewer signoff
- Re-run the hosted `/api/submission/proof` check after deployment and confirm it reports 100,000 processed candidates
- Publish or reproduce the MiniLM artifact through the documented precompute script; do not upload the raw 100K dataset publicly
- Rehearse the 30-minute architecture defense with every team member
- Prepare the portal fields and submit only after the final validator run; the last of at most three valid submissions counts

## Accuracy statement

Do not claim 95% accuracy or precision without labels. Report the measured runtime, validator result, manual-label proxy metrics, honeypot audit, and reasoning-review completion. Hidden NDCG/MAP/P@10 remain unknown until the organizers score the submission.

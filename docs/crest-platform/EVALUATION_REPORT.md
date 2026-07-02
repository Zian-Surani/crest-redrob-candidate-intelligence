# CREST Evaluation Report

Generated from persisted ranking `22`.

This is an internal QA artifact. It is not an official Redrob score, does not claim
access to hidden relevance labels, and should be read as reproducibility and
risk-reduction evidence only.

## Internal QA gate

- Artifact completeness score: **97.0/100**
- Visible engineering gate score: **100.0/100**
- Band: **internal-qa-complete**
- Hidden Redrob NDCG: **unknown**. This report reduces visible risk; it does not claim access to hidden labels.

### Uncertainty penalties

- `hidden_redrob_labels_unavailable`: -3.0 (No team can verify the official hidden NDCG before judging.)

## Full-run proof

- Scope: `full`
- Processed candidates: `100,000`
- Final rows: `100`
- Runtime: `131.869s` of a 300s budget
- Top candidate: `CAND_0077337` at score `98.377`
- Data mode: actual full-run snapshot, not sample/demo data

## General ranking risk checks

- PASS `top10_meet_experience_floor`
- PASS `top20_meet_experience_floor`
- PASS `top10_response_at_least_50`
- PASS `top20_response_at_least_50`
- PASS `top20_no_unavailable_low_response`
- PASS `top50_no_services_only`
- PASS `top50_no_unavailable_low_response`
- PASS `top100_no_services_only`
- PASS `top100_no_integrity_failures`

## Non-scoring calibration regressions

These candidate-ID checks are retained only to prevent previously observed failure
modes from reappearing. They are not presented as proof of hidden leaderboard
quality.

- PASS `CAND_0000031_top20`
- PASS `CAND_0042506_below_top30`
- PASS `CAND_0096142_reasonable_20_to_45`
- PASS `CAND_0007412_reasonable_30_to_60`
- PASS `CAND_0094759_excluded_or_below85`
- PASS `CAND_0093547_excluded`
- PASS `CAND_0067866_excluded`

## Reasoning quality

- Exact unique reasonings: `True`
- Opening-pattern variety >= 70: `True`
- Internal variable leaks absent: `True`
- Observed unique four-word openers: `90`

## Manual proxy calibration

{
  "available": true,
  "filled_rows": 50,
  "auto_prefilled_rows": 0,
  "rows": 50,
  "ndcg_at_10_proxy": 1.0,
  "ndcg_at_20_proxy": 0.945,
  "ndcg_at_50_proxy": 0.9856,
  "note": "Proxy only: this uses the team's review labels for sanity checking, not Redrob's hidden relevance labels."
}

## Remaining blockers

- None

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any

from app.config import settings
from app.evaluation import project_score
from app.main import _submission_readiness
from app.store import Store


SUBMISSION_FIELDS = ("candidate_id", "rank", "score", "reasoning")
AUDIT_ARTIFACTS = (
    "automated_audit_report.json",
    "automated_integrity_audit.csv",
    "automated_reasoning_audit.csv",
    "automated_top50_review.csv",
    "crest_submission.csv",
    "manual_review_top50.csv",
    "reasoning_audit_10.csv",
)


def _write_submission_csv(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(SUBMISSION_FIELDS)
        for item in results:
            writer.writerow([
                item["candidate_id"],
                item["rank"],
                f"{item['normalized_score']:.6f}",
                item["reasoning"],
            ])


def _write_report(path: Path, scorecard: dict[str, Any], ranking: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blockers = scorecard.get("blockers", [])
    blocker_text = "\n".join(f"- `{item}`" for item in blockers) if blockers else "- None"
    penalties = "\n".join(
        f"- `{item['name']}`: -{item['points']} ({item['reason']})"
        for item in scorecard.get("uncertainty_penalties", [])
    )
    canaries = scorecard["ranking_checks"]
    canary_text = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} `{name}`"
        for name, passed in canaries.items()
    )
    report = f"""# CREST Evaluation Report

Generated from persisted ranking `{ranking['id']}`.

## Honest score

- Win-readiness score: **{scorecard['score_out_of_100']}/100**
- Visible engineering gate score: **{scorecard['engineering_readiness_score']}/100**
- Band: **{scorecard['band']}**
- Hidden Redrob NDCG: **unknown**. This report reduces visible risk; it does not claim access to hidden labels.

### Uncertainty penalties

{penalties}

## Full-run proof

- Scope: `{ranking['scope']}`
- Processed candidates: `{ranking['processed_count']:,}`
- Final rows: `{len(ranking['results'])}`
- Runtime: `{ranking['duration_seconds']}s` of a 300s budget
- Top candidate: `{ranking['results'][0]['candidate_id']}` at score `{ranking['results'][0]['score']}`
- Data mode: actual full-run snapshot, not sample/demo data

## Canary checks

{canary_text}

## Reasoning quality

- Exact unique reasonings: `{scorecard['reasoning_checks']['all_reasonings_unique']}`
- Opening-pattern variety >= 70: `{scorecard['reasoning_checks']['opener_variety_at_least_70']}`
- Internal variable leaks absent: `{scorecard['reasoning_checks']['no_internal_leaks']}`
- Observed unique four-word openers: `{scorecard['observed']['reasoning_opener4_unique']}`

## Manual proxy calibration

{json.dumps(scorecard['manual_proxy'], indent=2)}

## Remaining blockers

{blocker_text}
"""
    path.write_text(report, encoding="utf-8")


def export_latest(data_dir: Path, sandbox_dir: Path, docs_dir: Path) -> dict[str, Any]:
    store = Store(settings.database_path)
    store.initialize()
    ranking = store.latest_ranking()
    if not ranking:
        raise RuntimeError("No persisted ranking found.")
    job = store.get_job(ranking["job_id"])
    if not job:
        raise RuntimeError(f"Job {ranking['job_id']} was not found.")

    data_dir.mkdir(parents=True, exist_ok=True)
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    _write_submission_csv(data_dir / "crest_submission.csv", ranking["results"])
    _write_submission_csv(sandbox_dir / "crest_submission.csv", ranking["results"])

    snapshot = {**ranking, "job": job}
    (sandbox_dir / "ranking_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    for filename in AUDIT_ARTIFACTS:
        source = data_dir / filename
        if source.exists():
            shutil.copy2(source, sandbox_dir / filename)

    readiness = _submission_readiness({**ranking, "job": job})
    scorecard = project_score(
        ranking,
        readiness,
        data_dir / "crest_submission.csv",
        data_dir / "manual_review_top50.csv",
    )
    (data_dir / "evaluation_proxy_report.json").write_text(
        json.dumps(scorecard, indent=2),
        encoding="utf-8",
    )
    (sandbox_dir / "evaluation_proxy_report.json").write_text(
        json.dumps(scorecard, indent=2),
        encoding="utf-8",
    )
    _write_report(docs_dir / "EVALUATION_REPORT.md", scorecard, ranking)
    return {
        "ranking_id": ranking["id"],
        "processed_count": ranking["processed_count"],
        "duration_seconds": ranking["duration_seconds"],
        "score_out_of_100": scorecard["score_out_of_100"],
        "blockers": scorecard["blockers"],
        "snapshot": str((sandbox_dir / "ranking_snapshot.json").resolve()),
        "report": str((docs_dir / "EVALUATION_REPORT.md").resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export latest CREST ranking artifacts.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--sandbox-dir", default="data/sandbox")
    parser.add_argument("--docs-dir", default="../docs/crest-platform")
    args = parser.parse_args()
    result = export_latest(Path(args.data_dir), Path(args.sandbox_dir), Path(args.docs_dir))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

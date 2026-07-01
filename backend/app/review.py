from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path
from typing import Any

from app.audit import automated_relevance_tier, reasoning_checks
from app.config import settings
from app.store import Store


LABEL_FIELDS = ("human_relevance_tier", "honeypot_flag", "reviewer_notes")
REASONING_LABEL_FIELDS = (
    "specific_facts_pass", "jd_connection_pass", "honest_concerns_pass",
    "no_hallucination_pass", "variation_pass", "rank_consistency_pass",
    "reviewer_notes",
)


def existing_labels(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["candidate_id"]: {field: row.get(field, "") for field in LABEL_FIELDS}
            for row in csv.DictReader(handle)
        }


def existing_reasoning_labels(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["candidate_id"]: {
                field: row.get(field, "") for field in REASONING_LABEL_FIELDS
            }
            for row in csv.DictReader(handle)
        }


def _prefilled_review_labels(result: dict[str, Any], job: dict[str, Any]) -> dict[str, str]:
    tier, rationale = automated_relevance_tier(result, job)
    concern = "no major generated concern"
    reasoning = str(result.get("reasoning", ""))
    if "primary concerns:" in reasoning:
        concern = reasoning.split("primary concerns:", 1)[1].split(".", 1)[0].strip()
    return {
        "human_relevance_tier": str(tier),
        "honeypot_flag": "TRUE" if result.get("disqualified") else "FALSE",
        "reviewer_notes": (
            "AUTO-PREFILL after rerank; verify manually before portal upload. "
            f"{rationale} {result.get('company')} {result.get('role')} "
            f"({result.get('years_experience')}yr, score {result.get('score')}, "
            f"availability {result.get('behavioral', {}).get('availability_score')}, "
            f"notice {result.get('notice_period_days')}d). Concern read: {concern}."
        ),
    }


def export_top_review(
    ranking: dict[str, Any], path: Path, top: int,
    job: dict[str, Any], auto_fill_empty: bool = False,
) -> None:
    labels = existing_labels(path)
    fields = [
        "rank", "candidate_id", "name", "role", "company", "location",
        "years_experience", "score", "semantic_similarity", "availability_score",
        "notice_period_days", "projected_cph_inr", "reasoning", *LABEL_FIELDS,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in ranking["results"][:top]:
            row_labels = labels.get(result["candidate_id"])
            if not row_labels and auto_fill_empty:
                row_labels = _prefilled_review_labels(result, job)
            if not row_labels:
                row_labels = {field: "" for field in LABEL_FIELDS}
            writer.writerow({
                "rank": result["rank"], "candidate_id": result["candidate_id"],
                "name": result["name"], "role": result["role"], "company": result["company"],
                "location": result["location"], "years_experience": result["years_experience"],
                "score": result["score"],
                "semantic_similarity": result.get("semantic_relevance", {}).get("similarity", ""),
                "availability_score": result["behavioral"]["availability_score"],
                "notice_period_days": result["notice_period_days"],
                "projected_cph_inr": result["projected_cph_inr"],
                "reasoning": result["reasoning"],
                **row_labels,
            })


def export_reasoning_sample(
    ranking: dict[str, Any], path: Path, size: int,
    seed: int, auto_fill_empty: bool = False,
) -> None:
    labels = existing_reasoning_labels(path)
    population = ranking["results"]
    selected = random.Random(seed).sample(population, min(size, len(population)))
    selected.sort(key=lambda item: item["rank"])
    scores = [float(item.get("score", 0)) for item in ranking["results"]]
    score_order_pass = all(left >= right for left, right in zip(scores, scores[1:]))
    variation_pass = len({str(item.get("reasoning", ""))[:60] for item in ranking["results"]}) >= max(50, len(ranking["results"]) // 2)
    fields = [
        "rank", "candidate_id", "name", "score", "reasoning",
        "specific_facts_pass", "jd_connection_pass", "honest_concerns_pass",
        "no_hallucination_pass", "variation_pass", "rank_consistency_pass", "reviewer_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in selected:
            row_labels = labels.get(result["candidate_id"])
            if not row_labels and auto_fill_empty:
                checks = reasoning_checks(result, score_order_pass)
                row_labels = {
                    "specific_facts_pass": str(checks["specific_facts_pass"]).upper(),
                    "jd_connection_pass": str(checks["jd_connection_pass"]).upper(),
                    "honest_concerns_pass": str(checks["honest_concerns_pass"]).upper(),
                    "no_hallucination_pass": str(checks["no_hallucination_pass"]).upper(),
                    "variation_pass": str(variation_pass).upper(),
                    "rank_consistency_pass": str(checks["rank_consistency_pass"]).upper(),
                    "reviewer_notes": "AUTO-PREFILL after rerank; verify manually before portal upload.",
                }
            if not row_labels:
                row_labels = {field: "" for field in REASONING_LABEL_FIELDS}
            writer.writerow({
                "rank": result["rank"], "candidate_id": result["candidate_id"],
                "name": result["name"], "score": result["score"],
                "reasoning": result["reasoning"],
                **row_labels,
            })


def evaluate_labels(path: Path) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    labeled = [row for row in rows if row.get("human_relevance_tier", "").strip()]
    print(f"Human-label coverage: {len(labeled)}/{len(rows)}")
    if len(labeled) != len(rows):
        print("Complete every human_relevance_tier (0-5) before using proxy metrics.")
        return
    relevances = [int(row["human_relevance_tier"]) for row in rows]

    def ndcg_at(k: int) -> float:
        actual = sum((2 ** rel - 1) / math.log2(index + 2) for index, rel in enumerate(relevances[:k]))
        ideal = sum(
            (2 ** rel - 1) / math.log2(index + 2)
            for index, rel in enumerate(sorted(relevances, reverse=True)[:k])
        )
        return actual / ideal if ideal else 0.0

    p10 = sum(rel >= 3 for rel in relevances[:10]) / min(10, len(relevances))
    print(f"Proxy NDCG@10: {ndcg_at(10):.4f}")
    print(f"Proxy NDCG@50: {ndcg_at(min(50, len(relevances))):.4f}")
    print(f"Proxy P@10: {p10:.4f}")
    print("These are calibration proxies from your labels, not the hidden competition score.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create human calibration and reasoning-review sheets.")
    parser.add_argument("--output", default="data/manual_review_top50.csv")
    parser.add_argument("--reasoning-output", default="data/reasoning_audit_10.csv")
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--reasoning-sample", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260623)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument(
        "--auto-fill-empty",
        action="store_true",
        help="Prefill rows not present in the existing manual sheets with deterministic audit labels.",
    )
    args = parser.parse_args()

    store = Store(settings.database_path)
    store.initialize()
    ranking = store.latest_ranking()
    if not ranking:
        raise SystemExit("No persisted ranking found. Run a ranking first.")
    job = store.get_job(ranking["job_id"])
    if not job:
        raise SystemExit(f"Job {ranking['job_id']} was not found.")
    output = Path(args.output)
    reasoning_output = Path(args.reasoning_output)
    export_top_review(ranking, output, args.top, job, args.auto_fill_empty)
    export_reasoning_sample(
        ranking, reasoning_output, args.reasoning_sample,
        args.seed, args.auto_fill_empty,
    )
    print(f"Wrote human calibration sheet: {output.resolve()}")
    print(f"Wrote blind reasoning sample: {reasoning_output.resolve()}")
    if args.evaluate:
        evaluate_labels(output)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path
from typing import Any

from app.config import settings
from app.store import Store


LABEL_FIELDS = ("human_relevance_tier", "honeypot_flag", "reviewer_notes")


def existing_labels(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["candidate_id"]: {field: row.get(field, "") for field in LABEL_FIELDS}
            for row in csv.DictReader(handle)
        }


def export_top_review(ranking: dict[str, Any], path: Path, top: int) -> None:
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
                **labels.get(result["candidate_id"], {field: "" for field in LABEL_FIELDS}),
            })


def export_reasoning_sample(ranking: dict[str, Any], path: Path, size: int, seed: int) -> None:
    population = ranking["results"]
    selected = random.Random(seed).sample(population, min(size, len(population)))
    selected.sort(key=lambda item: item["rank"])
    fields = [
        "rank", "candidate_id", "name", "score", "reasoning",
        "specific_facts_pass", "jd_connection_pass", "honest_concerns_pass",
        "no_hallucination_pass", "variation_pass", "rank_consistency_pass", "reviewer_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in selected:
            writer.writerow({
                "rank": result["rank"], "candidate_id": result["candidate_id"],
                "name": result["name"], "score": result["score"],
                "reasoning": result["reasoning"],
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
    args = parser.parse_args()

    store = Store(settings.database_path)
    store.initialize()
    ranking = store.latest_ranking()
    if not ranking:
        raise SystemExit("No persisted ranking found. Run a ranking first.")
    output = Path(args.output)
    reasoning_output = Path(args.reasoning_output)
    export_top_review(ranking, output, args.top)
    export_reasoning_sample(ranking, reasoning_output, args.reasoning_sample, args.seed)
    print(f"Wrote human calibration sheet: {output.resolve()}")
    print(f"Wrote blind reasoning sample: {reasoning_output.resolve()}")
    if args.evaluate:
        evaluate_labels(output)


if __name__ == "__main__":
    main()

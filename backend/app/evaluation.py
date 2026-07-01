from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any


LEAK_PATTERN = re.compile(
    r"flask,\s*pytorch,\s*sklearn|career delivery references|career evidence:|"
    r"raw_fit|component_max|matched_requirements",
    re.IGNORECASE,
)


def _points(condition: bool, value: float) -> float:
    return value if condition else 0.0


def _csv_checks(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"present": False, "score": 0.0, "checks": {"present": False}}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ranks = [int(row.get("rank", 0) or 0) for row in rows]
    scores = [float(row.get("score", 0) or 0) for row in rows]
    reasonings = [str(row.get("reasoning", "")) for row in rows]
    checks = {
        "present": True,
        "exactly_100_rows": len(rows) == 100,
        "sequential_ranks": ranks == list(range(1, 101)),
        "unique_candidate_ids": len({row.get("candidate_id") for row in rows}) == len(rows),
        "scores_non_increasing": all(left >= right for left, right in zip(scores, scores[1:])),
        "reasoning_non_empty": all(reasoning.strip() for reasoning in reasonings),
    }
    score = sum(_points(value, 22 / 6) for value in checks.values())
    return {"present": True, "score": round(score, 1), "checks": checks}


def _ndcg(labels: list[int], k: int) -> float:
    observed = labels[:k]
    ideal = sorted(labels, reverse=True)[:k]
    if not observed or not any(ideal):
        return 0.0
    dcg = sum((2**label - 1) / math.log2(index + 2) for index, label in enumerate(observed))
    idcg = sum((2**label - 1) / math.log2(index + 2) for index, label in enumerate(ideal))
    return round(dcg / idcg, 4) if idcg else 0.0


def _manual_proxy(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {
            "available": False,
            "note": "Manual top-50 proxy sheet not found; hidden Redrob labels remain unavailable.",
        }
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    labels = []
    filled_rows = 0
    auto_prefilled_rows = 0
    for row in rows:
        value = str(row.get("human_relevance_tier", "")).strip()
        if value:
            filled_rows += 1
        if "auto-prefill" in str(row.get("reviewer_notes", "")).lower():
            auto_prefilled_rows += 1
        try:
            labels.append(max(0, min(5, int(float(value or 0)))))
        except ValueError:
            labels.append(0)
    return {
        "available": True,
        "filled_rows": filled_rows,
        "auto_prefilled_rows": auto_prefilled_rows,
        "rows": len(rows),
        "ndcg_at_10_proxy": _ndcg(labels, 10),
        "ndcg_at_20_proxy": _ndcg(labels, 20),
        "ndcg_at_50_proxy": _ndcg(labels, 50),
        "note": (
            "Proxy only: this uses the team's review labels for sanity checking, "
            "not Redrob's hidden relevance labels."
        ),
    }


def project_score(
    ranking: dict[str, Any],
    readiness: dict[str, Any],
    submission_csv_path: Path | None = None,
    manual_review_path: Path | None = None,
) -> dict[str, Any]:
    results = ranking.get("results", [])
    positions = {item.get("candidate_id"): int(item.get("rank", 10_000)) for item in results}
    top10 = results[:10]
    top20 = results[:20]
    top50 = results[:50]
    reasonings = [str(item.get("reasoning", "")) for item in results]
    opener4 = {" ".join(reasoning.split()[:4]) for reasoning in reasonings if reasoning.strip()}
    csv_report = _csv_checks(submission_csv_path)

    canaries = {
        "CAND_0000031_top20": positions.get("CAND_0000031", 10_000) <= 20,
        "CAND_0042506_below_top30": positions.get("CAND_0042506", 10_000) > 30,
        "CAND_0096142_reasonable_20_to_45": 20 <= positions.get("CAND_0096142", 10_000) <= 45,
        "CAND_0007412_reasonable_30_to_60": 30 <= positions.get("CAND_0007412", 10_000) <= 60,
        "CAND_0094759_excluded_or_below85": positions.get("CAND_0094759", 10_000) > 85,
        "CAND_0093547_excluded": "CAND_0093547" not in positions,
        "CAND_0067866_excluded": "CAND_0067866" not in positions,
    }
    ranking_checks = {
        **canaries,
        "top10_meet_experience_floor": all(float(item.get("years_experience", 0) or 0) >= 5 for item in top10),
        "top10_response_at_least_50": all(float(item.get("response_rate", 0) or 0) >= 0.50 for item in top10),
        "top20_no_unavailable_low_response": all(
            bool(item.get("open_to_work")) or float(item.get("response_rate", 0) or 0) >= 0.60
            for item in top20
        ),
        "top50_no_services_only": not any(bool(item.get("services_only")) for item in top50),
    }
    reasoning_checks = {
        "all_reasonings_unique": len(set(reasonings)) == len(reasonings) == 100,
        "opener_variety_at_least_70": len(opener4) >= 70,
        "no_internal_leaks": not any(LEAK_PATTERN.search(reasoning) for reasoning in reasonings),
        "concerns_in_risky_rows": all(
            "concern" in str(item.get("reasoning", "")).lower()
            for item in results
            if (
                int(item.get("notice_period_days", 0) or 0) > 30
                or float(item.get("response_rate", 0) or 0) < 0.25
                or item.get("missing_requirements")
            )
        ),
    }
    operational_checks = {
        "full_100k_run": ranking.get("scope") == "full" and ranking.get("processed_count") == 100_000,
        "runtime_under_300s": float(ranking.get("duration_seconds", 9999) or 9999) <= 300,
        "automated_readiness_100": readiness.get("automated_score") == 100,
        "handoff_readiness_100": readiness.get("handoff_score") == 100,
        "no_demo_sample_mode": len(results) == 100 and ranking.get("processed_count") == 100_000,
    }

    ranking_score = sum(_points(value, 28 / len(ranking_checks)) for value in ranking_checks.values())
    reasoning_score = sum(_points(value, 20 / len(reasoning_checks)) for value in reasoning_checks.values())
    operational_score = sum(_points(value, 30 / len(operational_checks)) for value in operational_checks.values())
    engineering_total = csv_report["score"] + ranking_score + reasoning_score + operational_score
    manual_proxy = _manual_proxy(manual_review_path)
    uncertainty_penalties: list[dict[str, Any]] = [
        {
            "name": "hidden_redrob_labels_unavailable",
            "points": 3.0,
            "reason": "No team can verify the official hidden NDCG before judging.",
        },
    ]
    if manual_proxy.get("auto_prefilled_rows", 0):
        uncertainty_penalties.append({
            "name": "manual_review_rows_need_human_reskim",
            "points": 1.0,
            "reason": f"{manual_proxy['auto_prefilled_rows']} top-50 review rows were prefilled after rerank.",
        })
    if not readiness.get("portal_ready"):
        uncertainty_penalties.append({
            "name": "portal_handoff_not_ready",
            "points": 2.0,
            "reason": "One or more handoff checks is still incomplete.",
        })
    win_score = max(
        0.0,
        engineering_total - sum(float(item["points"]) for item in uncertainty_penalties),
    )
    blockers = [
        name for group in (ranking_checks, reasoning_checks, operational_checks)
        for name, passed in group.items()
        if not passed
    ]
    return {
        "score_out_of_100": round(win_score, 1),
        "engineering_readiness_score": round(engineering_total, 1),
        "uncertainty_penalties": uncertainty_penalties,
        "band": "winner-ready" if win_score >= 96 else "strong" if win_score >= 90 else "needs-work",
        "csv": csv_report,
        "ranking_checks": ranking_checks,
        "reasoning_checks": reasoning_checks,
        "operational_checks": operational_checks,
        "manual_proxy": manual_proxy,
        "observed": {
            "reasoning_opener4_unique": len(opener4),
            "rows": len(results),
            "processed_count": ranking.get("processed_count"),
            "duration_seconds": ranking.get("duration_seconds"),
            "top_candidate": results[0].get("candidate_id") if results else None,
        },
        "blockers": blockers,
        "disclaimer": (
            "This is a brutal engineering/readiness score. It cannot know Redrob's hidden "
            "NDCG labels, so it should be used to reduce visible risk, not as a guaranteed leaderboard score."
        ),
    }

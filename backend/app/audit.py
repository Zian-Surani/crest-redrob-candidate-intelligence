from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.config import settings
from app.repository import CandidateRepository
from app.services.integrity import analyze_integrity
from app.store import Store


REGRESSION_IDS = {
    "available_product_candidate": "CAND_0000031",
    "unavailable_candidate": "CAND_0094759",
    "experience_contradiction": "CAND_0093547",
}


def automated_relevance_tier(result: dict[str, Any], job: dict[str, Any]) -> tuple[int, str]:
    requirements = result.get("matched_requirements", [])
    strong_coverage = sum(
        item.get("status") != "missing" and float(item.get("score", 0)) >= 55
        for item in requirements
    )
    relevant_roles = int(result.get("career_evidence", {}).get("relevant_product_role_count", 0))
    availability = float(result.get("behavioral", {}).get("availability_score", 0))
    years = float(result.get("years_experience", 0))
    minimum = float(job.get("parsed", {}).get("experience_min", 5))
    maximum = float(job.get("parsed", {}).get("experience_max", 9))
    flexible_floor = max(3.5, minimum - 1.5)

    if result.get("disqualified") or years < flexible_floor:
        return 0, "Fails integrity or flexible experience floor."
    if strong_coverage >= 4 and relevant_roles >= 2 and availability >= 60:
        return 5, "All core capabilities, repeated product delivery, and recruiter availability."
    if strong_coverage >= 3 and relevant_roles >= 2 and availability >= 45:
        return 4, "Strong core coverage and repeated product-system delivery."
    if strong_coverage >= 2 and relevant_roles >= 1 and flexible_floor <= years <= maximum + 3:
        return 3, "Credible adjacent fit with at least one relevant product role."
    if strong_coverage >= 1 or relevant_roles >= 1:
        return 2, "Partial evidence; important capability or availability gaps remain."
    return 1, "Weak direct evidence for the role."


def reasoning_checks(result: dict[str, Any], score_order_pass: bool) -> dict[str, bool]:
    reasoning = str(result.get("reasoning", ""))
    profile = result.get("profile", {})
    role = str(result.get("role", ""))
    company = str(result.get("company", ""))
    years = float(result.get("years_experience", 0))
    requirements = result.get("matched_requirements", [])
    supported_evidence = [
        str(item.get("evidence", ""))
        for item in requirements
        if item.get("status") != "missing"
    ]
    concerns_required = []
    if int(result.get("notice_period_days", 0)) > 30:
        concerns_required.append("notice")
    if float(result.get("response_rate", 0)) < 0.25:
        concerns_required.append("response")
    if result.get("missing_requirements"):
        concerns_required.append("missing")
    if result.get("services_only"):
        concerns_required.append("services-only")

    years_present = (
        f"{years:g} years" in reasoning
        or f"{years:g}-year" in reasoning
    )
    facts_pass = role in reasoning and company in reasoning and years_present
    jd_pass = any(
        str(item.get("requirement", "")) in reasoning
        for item in requirements
        if item.get("status") != "missing"
    )
    concerns_pass = all(marker in reasoning.lower() for marker in concerns_required[:2])
    evidence_pass = not supported_evidence or any(item in reasoning for item in supported_evidence)
    positive_open_claim = re.search(
        r"(?<!not marked )\bopen to work\b",
        reasoning.lower(),
    )
    open_claim_pass = not (positive_open_claim and not bool(result.get("open_to_work")))
    profile_pass = str(profile.get("current_title", role)) == role
    internal_terms = (
        "Career evidence:",
        "Profile mention:",
        "career delivery references",
        "sklearn",
        "raw_fit",
        "component_max",
        "matched_requirements",
    )
    internal_pass = not any(term in reasoning for term in internal_terms)
    return {
        "specific_facts_pass": facts_pass and profile_pass,
        "jd_connection_pass": jd_pass,
        "honest_concerns_pass": concerns_pass,
        "no_hallucination_pass": evidence_pass and open_claim_pass and internal_pass,
        "rank_consistency_pass": score_order_pass,
    }


def integrity_category(flags: list[dict[str, Any]]) -> str:
    evidence = " ".join(str(flag.get("evidence", "")) for flag in flags).lower()
    if "profile declares" in evidence:
        return "Experience claim contradiction"
    if "ends before" in evidence or "dates imply" in evidence:
        return "Temporal contradiction"
    if "marked expert" in evidence:
        return "Impossible skill-duration claim"
    if "ai-heavy" in evidence or "listed skills" in evidence:
        return "Unsupported skill inventory"
    if "declared experience" in evidence:
        return "Experience-history mismatch"
    return "Combined integrity risk"


def integrity_assessment(flags: list[dict[str, Any]]) -> tuple[str, str]:
    evidence = " ".join(str(flag.get("evidence", "")) for flag in flags).lower()
    objective_markers = ("ends before", "marked expert", "profile declares")
    if any(marker in evidence for marker in objective_markers):
        return "exclude", "low"
    if "ai-heavy" in evidence and "not supported" in evidence:
        return "exclude", "medium"
    return "human_review", "medium"


def select_integrity_sample(records: list[dict[str, Any]], size: int, seed: int) -> list[dict[str, Any]]:
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_category[record["category"]].append(record)
    selected: list[dict[str, Any]] = []
    per_category = max(1, size // max(1, len(by_category)))
    for category in sorted(by_category):
        ordered = sorted(
            by_category[category],
            key=lambda item: (-item["risk_score"], item["candidate_id"]),
        )
        selected.extend(ordered[:per_category])
    selected_ids = {item["candidate_id"] for item in selected}
    remaining = [item for item in records if item["candidate_id"] not in selected_ids]
    random.Random(seed).shuffle(remaining)
    selected.extend(remaining[: max(0, size - len(selected))])
    return sorted(selected[:size], key=lambda item: (-item["risk_score"], item["candidate_id"]))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError(f"No audit rows were generated for {path}.")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_audit(output_dir: Path, integrity_sample_size: int = 50) -> dict[str, Any]:
    store = Store(settings.database_path)
    store.initialize()
    ranking = store.latest_ranking()
    if not ranking:
        raise RuntimeError("No persisted ranking exists. Run the full ranking first.")
    job = store.get_job(ranking["job_id"])
    if not job:
        raise RuntimeError(f"Job {ranking['job_id']} was not found.")
    results = ranking["results"]
    scores = [float(item["score"]) for item in results]
    score_order_pass = all(left >= right for left, right in zip(scores, scores[1:]))
    prefixes = [str(item["reasoning"])[:60] for item in results]
    variation_pass = len(set(prefixes)) >= max(50, len(results) // 2)

    reasoning_rows = []
    reasoning_failures: Counter[str] = Counter()
    for result in results:
        checks = reasoning_checks(result, score_order_pass)
        for name, passed in checks.items():
            if not passed:
                reasoning_failures[name] += 1
        reasoning_rows.append({
            "rank": result["rank"],
            "candidate_id": result["candidate_id"],
            "reasoning": result["reasoning"],
            **checks,
            "variation_pass": variation_pass,
            "automated_review_pass": all(checks.values()) and variation_pass,
        })
    write_csv(output_dir / "automated_reasoning_audit.csv", reasoning_rows)

    relevance_rows = []
    tier_counts: Counter[int] = Counter()
    for result in results[:50]:
        tier, rationale = automated_relevance_tier(result, job)
        tier_counts[tier] += 1
        relevance_rows.append({
            "rank": result["rank"],
            "candidate_id": result["candidate_id"],
            "name": result["name"],
            "role": result["role"],
            "company": result["company"],
            "years_experience": result["years_experience"],
            "score": result["score"],
            "availability_score": result["behavioral"]["availability_score"],
            "core_requirements_evidenced": sum(
                item["status"] != "missing" and float(item["score"]) >= 55
                for item in result["matched_requirements"]
            ),
            "relevant_product_roles": result.get("career_evidence", {}).get(
                "relevant_product_role_count", 0
            ),
            "automated_relevance_tier": tier,
            "automated_rationale": rationale,
            "human_relevance_tier": "",
            "human_reviewer_notes": "",
        })
    write_csv(output_dir / "automated_top50_review.csv", relevance_rows)

    repository = CandidateRepository(settings.data_dir)
    excluded = []
    for candidate in repository.iter_candidates("full"):
        integrity = analyze_integrity(candidate)
        if integrity["passed"]:
            continue
        profile = candidate.get("profile", {})
        recommendation, false_positive_risk = integrity_assessment(integrity["flags"])
        excluded.append({
            "candidate_id": candidate.get("candidate_id"),
            "name": profile.get("anonymized_name", ""),
            "role": profile.get("current_title", ""),
            "company": profile.get("current_company", ""),
            "declared_years": profile.get("years_of_experience", ""),
            "risk_score": integrity["risk_score"],
            "category": integrity_category(integrity["flags"]),
            "evidence": " | ".join(flag["evidence"] for flag in integrity["flags"]),
            "automated_recommendation": recommendation,
            "false_positive_risk": false_positive_risk,
            "human_decision": "",
            "human_reviewer_notes": "",
        })
    integrity_sample = select_integrity_sample(excluded, integrity_sample_size, 20260624)
    write_csv(output_dir / "automated_integrity_audit.csv", integrity_sample)

    positions = {item["candidate_id"]: item["rank"] for item in results}
    excluded_ids = {item["candidate_id"] for item in excluded}
    regression_checks = {
        "available_product_candidate_top20": positions.get(
            REGRESSION_IDS["available_product_candidate"], 10_000
        ) <= 20,
        "unavailable_candidate_below85_or_excluded": positions.get(
            REGRESSION_IDS["unavailable_candidate"], 10_000
        ) > 85,
        "experience_contradiction_excluded": (
            REGRESSION_IDS["experience_contradiction"] in excluded_ids
            and REGRESSION_IDS["experience_contradiction"] not in positions
        ),
    }
    checks = {
        "exactly_100_results": len(results) == 100,
        "sequential_ranks": [item["rank"] for item in results] == list(range(1, 101)),
        "unique_candidate_ids": len({item["candidate_id"] for item in results}) == len(results),
        "scores_non_increasing": score_order_pass,
        "all_reasonings_non_empty": all(str(item["reasoning"]).strip() for item in results),
        "all_reasonings_unique": len({item["reasoning"] for item in results}) == len(results),
        "reasoning_prefix_variation": variation_pass,
        "reasoning_facts_grounded": not reasoning_failures,
        **regression_checks,
    }
    report = {
        "audit_version": 1,
        "ranking_id": ranking["id"],
        "processed_count": ranking["processed_count"],
        "duration_seconds": ranking["duration_seconds"],
        "checks": checks,
        "passed": all(checks.values()),
        "reasoning": {
            "rows_checked": len(reasoning_rows),
            "unique_60_character_prefixes": len(set(prefixes)),
            "failure_counts": dict(reasoning_failures),
        },
        "automated_relevance_tiers": {
            str(tier): count for tier, count in sorted(tier_counts.items(), reverse=True)
        },
        "integrity": {
            "excluded_profiles": len(excluded),
            "sampled_for_review": len(integrity_sample),
            "categories": dict(Counter(item["category"] for item in excluded)),
            "sample_recommendations": dict(
                Counter(item["automated_recommendation"] for item in integrity_sample)
            ),
            "human_signoff_required": True,
        },
        "artifacts": {
            "reasoning": "automated_reasoning_audit.csv",
            "top50": "automated_top50_review.csv",
            "integrity": "automated_integrity_audit.csv",
        },
    }
    report_path = output_dir / "automated_audit_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the latest CREST ranking and exclusions.")
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--integrity-sample-size", type=int, default=50)
    args = parser.parse_args()
    report = run_audit(Path(args.output_dir), args.integrity_sample_size)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

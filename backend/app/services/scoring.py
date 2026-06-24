from __future__ import annotations

import heapq
import math
import re
import time
from collections import Counter
from datetime import date
from typing import Any

from app.repository import CandidateRepository
from app.services.integrity import analyze_integrity
from app.services.jd_parser import SKILL_GROUPS, group_hits
from app.services.semantic import SemanticScorer


SERVICE_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "mindtree", "ltimindtree", "hcl", "tech mahindra"
}
ROLE_TERMS = (
    "ai engineer", "ml engineer", "machine learning", "data scientist", "nlp engineer",
    "search engineer", "recommendation", "ranking", "applied scientist", "software engineer"
)
PRODUCTION_TERMS = (
    "production", "deployed", "shipped", "serving", "users", "latency", "scale",
    "million", "billion", "on-call", "monitoring", "a/b", "ab test"
)
TRANSFERABLE_SYSTEM_TERMS = (
    "search", "retrieval", "ranking", "recommendation", "recommender",
    "discovery feed", "learning-to-rank", "learning to rank",
)
EXTERNAL_TERMS = ("open source", "github", "paper", "publication", "conference", "speaker", "patent")
PROFICIENCY = {"beginner": 0.35, "intermediate": 0.58, "advanced": 0.82, "expert": 1.0}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def _date_recency(value: str) -> float:
    try:
        days = max(0, (date.today() - date.fromisoformat(value)).days)
    except (TypeError, ValueError):
        return 0.35
    return _clamp(1 - days / 240)


def _candidate_text(candidate: dict[str, Any]) -> tuple[str, str, str]:
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skill_text = " ".join(str(item.get("name", "")) for item in candidate.get("skills", []))
    career_text = " ".join(
        f"{role.get('title', '')} {role.get('company', '')} {role.get('industry', '')} "
        f"{role.get('description', '')}" for role in career
    )
    profile_text = " ".join(
        str(profile.get(field, ""))
        for field in ("headline", "summary", "current_title", "current_company", "current_industry")
    )
    return profile_text.lower(), career_text.lower(), skill_text.lower()


def _skill_name_matches(name: str, terms: tuple[str, ...]) -> bool:
    """Match meaningful skill phrases without short-name substring collisions."""
    normalized_name = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    for term in terms:
        normalized_term = re.sub(r"[^a-z0-9]+", " ", term.lower()).strip()
        if normalized_name == normalized_term:
            return True
        if len(normalized_term) >= 4 and normalized_term in normalized_name:
            return True
    return False


class CandidateScorer:
    def __init__(self, semantic: SemanticScorer | None = None):
        self.semantic = semantic

    def prepare_job(self, job: dict[str, Any]) -> bool:
        if not self.semantic:
            return False
        parsed = job.get("parsed", {})
        semantic_query = (
            f"Role: {job.get('title', '')}. "
            f"Required capabilities: {', '.join(parsed.get('required_skills', []))}. "
            f"Preferred capabilities: {', '.join(parsed.get('preferred_skills', []))}. "
            f"Experience: {parsed.get('experience_min', '')}-{parsed.get('experience_max', '')} years. "
            f"Role context: {str(job.get('description', ''))[:1_200]}"
        )
        return self.semantic.prepare_job(semantic_query)

    def evaluate(self, candidate: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
        profile = candidate.get("profile", {})
        signals = candidate.get("redrob_signals", {})
        career = candidate.get("career_history", [])
        skills = candidate.get("skills", [])
        parsed = job.get("parsed", {})
        profile_text, career_text, skill_text = _candidate_text(candidate)
        full_text = f"{profile_text} {career_text} {skill_text}"

        integrity = analyze_integrity(candidate)
        components: dict[str, float] = {}
        semantic_similarity = (
            self.semantic.similarity(str(candidate.get("candidate_id", "")))
            if self.semantic else None
        )

        title = str(profile.get("current_title", "")).lower()
        role_fit = 1.0 if any(term in title for term in ROLE_TERMS) else 0.25
        production_hits = [term for term in PRODUCTION_TERMS if term in career_text]
        production_fit = min(1.0, len(production_hits) / 4)
        relevant_career_groups = [
            group for group in parsed.get("required_skills", []) + parsed.get("preferred_skills", [])
            if group_hits(career_text, group)
        ]
        all_groups = max(1, len(parsed.get("required_skills", [])))
        evidence_fit = min(1.0, len(relevant_career_groups) / all_groups)
        product_roles = [
            role for role in career
            if str(role.get("industry", "")).lower() != "it services"
            and str(role.get("company", "")).lower() not in SERVICE_COMPANIES
        ]
        product_ratio = len(product_roles) / max(1, len(career))
        relevant_product_roles = [
            role for role in product_roles
            if any(
                term in (
                    f"{role.get('title', '')} {role.get('description', '')}"
                ).lower()
                for term in TRANSFERABLE_SYSTEM_TERMS
            )
        ]
        transferable_system_fit = min(1.0, len(relevant_product_roles) / 3)
        # The JD explicitly treats shipped search/recommendation systems as
        # transferable evidence even when a profile omits vendor keywords.
        if production_fit >= 0.5:
            evidence_fit = max(evidence_fit, transferable_system_fit * 0.78)
        if semantic_similarity is None:
            career_score = 40 * (
                role_fit * 0.20 + production_fit * 0.28
                + evidence_fit * 0.32 + product_ratio * 0.20
            )
        else:
            career_score = 40 * (
                role_fit * 0.16 + production_fit * 0.23 + evidence_fit * 0.25
                + product_ratio * 0.16 + semantic_similarity * 0.20
            )
        career_score = min(
            40,
            career_score + 8 * transferable_system_fit * product_ratio,
        )
        services_only = bool(career) and not product_roles
        if services_only:
            career_score *= 0.58
        components["career_fit"] = round(career_score, 2)

        matched_requirements: list[dict[str, Any]] = []
        missing_requirements: list[str] = []
        requirement_scores = []
        for group in parsed.get("required_skills", []):
            text_hits = group_hits(full_text, group)
            career_hits = group_hits(career_text, group)
            matching_skills = []
            for item in skills:
                name = str(item.get("name", "")).lower()
                if _skill_name_matches(name, SKILL_GROUPS.get(group, ())):
                    matching_skills.append(item)
            if matching_skills:
                best = max(
                    matching_skills,
                    key=lambda item: (
                        PROFICIENCY.get(str(item.get("proficiency", "")).lower(), 0),
                        int(item.get("duration_months", 0) or 0),
                        int(item.get("endorsements", 0) or 0),
                    ),
                )
                depth = (
                    PROFICIENCY.get(str(best.get("proficiency", "")).lower(), 0.3) * 0.45
                    + min(1, int(best.get("duration_months", 0) or 0) / 36) * 0.35
                    + min(1, int(best.get("endorsements", 0) or 0) / 30) * 0.20
                )
                status = "exact" if career_hits else "semantic"
                evidence = (
                    f"{best.get('name')} · {best.get('duration_months', 0)} months · "
                    f"{best.get('proficiency', 'listed')}"
                )
            elif career_hits:
                depth = min(0.92, 0.58 + 0.08 * len(career_hits))
                status = "semantic"
                evidence = f"Career evidence: {', '.join(career_hits[:3])}"
            elif text_hits:
                depth = 0.38
                status = "semantic"
                evidence = f"Profile mention: {', '.join(text_hits[:2])}"
            else:
                depth = 0.0
                status = "missing"
                evidence = "Not evidenced in profile"
                missing_requirements.append(group)
            requirement_scores.append(depth)
            matched_requirements.append({
                "requirement": group, "status": status, "evidence": evidence,
                "score": round(depth * 100, 1),
            })
        skill_score = 25 * (sum(requirement_scores) / max(1, len(requirement_scores)))
        components["skill_depth"] = round(skill_score, 2)

        years = float(profile.get("years_of_experience", 0) or 0)
        minimum = float(parsed.get("experience_min", 3))
        maximum = float(parsed.get("experience_max", 12))
        midpoint = (minimum + maximum) / 2
        if minimum <= years <= maximum:
            experience_fit = 1 - abs(years - midpoint) / max(4, maximum - minimum) * 0.18
        elif years < minimum:
            experience_fit = max(0.1, 1 - (minimum - years) * 0.22)
        else:
            experience_fit = max(0.45, 1 - (years - maximum) * 0.08)
        components["experience_fit"] = round(15 * experience_fit, 2)

        location = str(profile.get("location", "")).lower()
        country = str(profile.get("country", "")).lower()
        target_locations = [str(item).lower() for item in parsed.get("locations", [])]
        exact_location = any(item and (item in location or location in item) for item in target_locations)
        india_fit = country == "india"
        relocation = bool(signals.get("willing_to_relocate"))
        if exact_location:
            location_fit = 1.0
        elif india_fit and relocation:
            location_fit = 0.82
        elif india_fit:
            location_fit = 0.65
        elif relocation:
            location_fit = 0.42
        else:
            location_fit = 0.08
        components["location_fit"] = round(10 * location_fit, 2)

        github = float(signals.get("github_activity_score", -1) or -1)
        external_hits = sum(term in full_text for term in EXTERNAL_TERMS)
        external_fit = (
            (0.5 if github < 0 else min(1, github / 65)) * 0.6
            + min(1, external_hits / 2) * 0.4
        )
        components["external_validation"] = round(10 * external_fit, 2)

        raw_fit = sum(components.values())
        if "research" in str(profile.get("current_industry", "")).lower() and not production_hits:
            raw_fit *= 0.7
        if not any(term in full_text for term in ("retrieval", "search", "ranking", "recommend")):
            raw_fit *= 0.72

        behavioral = self._behavior(signals)
        final_score = raw_fit * behavioral["multiplier"] * integrity["penalty"]
        final_score = round(_clamp(final_score, 0, 100), 3)

        cph = self._cost_per_hire(signals, job)
        reasoning = self._reasoning(
            str(candidate.get("candidate_id", "")), profile, signals, components,
            matched_requirements, missing_requirements, services_only, integrity,
            production_hits, len(relevant_product_roles),
        )
        questions = self._questions(profile, matched_requirements, missing_requirements)

        result = {
            "candidate_id": candidate.get("candidate_id"),
            "name": profile.get("anonymized_name", candidate.get("candidate_id")),
            "role": profile.get("current_title", "Unknown role"),
            "company": profile.get("current_company", "Unknown company"),
            "location": profile.get("location", "Unknown"),
            "country": profile.get("country", ""),
            "years_experience": years,
            "score": final_score,
            "normalized_score": round(final_score / 100, 6),
            "raw_fit": round(raw_fit, 3),
            "semantic_relevance": {
                "enabled": semantic_similarity is not None,
                "similarity": round(semantic_similarity * 100, 1) if semantic_similarity is not None else None,
                "model": self.semantic.model_name if self.semantic and semantic_similarity is not None else None,
                "explanation_policy": "Retrieval signal only; human-facing claims remain evidence-derived.",
            },
            "components": components,
            "component_max": {
                "career_fit": 40, "skill_depth": 25, "experience_fit": 15,
                "location_fit": 10, "external_validation": 10,
            },
            "behavioral": behavioral,
            "integrity": integrity,
            "projected_cph_inr": cph["amount"],
            "cph_breakdown": cph,
            "notice_period_days": int(signals.get("notice_period_days", 0) or 0),
            "response_rate": round(float(signals.get("recruiter_response_rate", 0) or 0), 3),
            "open_to_work": bool(signals.get("open_to_work_flag")),
            "salary_range_lpa": signals.get("expected_salary_range_inr_lpa", {"min": 0, "max": 0}),
            "matched_requirements": matched_requirements,
            "missing_requirements": missing_requirements,
            "reasoning": reasoning,
            "interview_questions": questions,
            "profile": profile,
            "career_history": career,
            "skills": skills,
            "redrob_signals": signals,
            "services_only": services_only,
            "career_evidence": {
                "product_role_count": len(product_roles),
                "relevant_product_role_count": len(relevant_product_roles),
                "transferable_system_fit": round(transferable_system_fit, 3),
            },
            "disqualified": not integrity["passed"],
        }
        return result

    @staticmethod
    def _behavior(signals: dict[str, Any]) -> dict[str, Any]:
        response = _clamp(float(signals.get("recruiter_response_rate", 0) or 0))
        response_time = float(signals.get("avg_response_time_hours", 168) or 168)
        response_speed = _clamp(1 - response_time / 240)
        active = _date_recency(str(signals.get("last_active_date", "")))
        open_to_work = 1.0 if signals.get("open_to_work_flag") else 0.18
        interview = _clamp(float(signals.get("interview_completion_rate", 0.5) or 0.5))
        offer_raw = float(signals.get("offer_acceptance_rate", -1) or -1)
        offer = 0.62 if offer_raw < 0 else _clamp(offer_raw)
        completeness = _clamp(float(signals.get("profile_completeness_score", 50) or 50) / 100)
        verified = sum(bool(signals.get(field)) for field in ("verified_email", "verified_phone", "linkedin_connected")) / 3
        quality = (
            response * 0.24 + response_speed * 0.08 + active * 0.15 + open_to_work * 0.16
            + interview * 0.17 + offer * 0.08 + completeness * 0.07 + verified * 0.05
        )
        availability = response * 0.35 + active * 0.25 + open_to_work * 0.25 + interview * 0.15
        ranking_quality = quality * 0.65 + availability * 0.35
        return {
            "quality": round(quality, 3),
            "ranking_quality": round(ranking_quality, 3),
            "multiplier": round(min(1.08, 0.52 + ranking_quality * 0.66), 3),
            "availability_score": round(availability * 100, 1),
            "last_active_score": round(active * 100, 1),
            "response_score": round(response * 100, 1),
            "interview_show_rate": round(interview * 100, 1),
            "offer_acceptance_rate": None if offer_raw < 0 else round(offer_raw * 100, 1),
        }

    @staticmethod
    def _cost_per_hire(signals: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
        response = max(0.08, float(signals.get("recruiter_response_rate", 0) or 0))
        interview = _clamp(float(signals.get("interview_completion_rate", 0.5) or 0.5))
        offer_raw = float(signals.get("offer_acceptance_rate", -1) or -1)
        offer = 0.62 if offer_raw < 0 else _clamp(offer_raw)
        notice = int(signals.get("notice_period_days", 60) or 60)
        touches = min(12.0, 1 / response)
        recruiter_cost = 4_500 + touches * 1_050
        vacancy_cost = min(180, notice + 14) * 760
        dropout_risk_cost = (1 - interview) * 18_000 + (1 - offer) * 22_000
        salary = signals.get("expected_salary_range_inr_lpa", {}) or {}
        expected_min = float(salary.get("min", 0) or 0)
        salary_max = float(job.get("salary_max_lpa", 40) or 40)
        salary_mismatch = max(0, expected_min - salary_max) * 4_000
        amount = int(round(12_000 + recruiter_cost + vacancy_cost + dropout_risk_cost + salary_mismatch, -2))
        return {
            "amount": amount,
            "recruiter_coordination": int(round(recruiter_cost)),
            "vacancy_delay": int(round(vacancy_cost)),
            "dropout_risk": int(round(dropout_risk_cost)),
            "salary_mismatch": int(round(salary_mismatch)),
            "estimated_touchpoints": round(touches, 1),
            "benchmark_inr": 110_000,
            "savings_vs_benchmark": 110_000 - amount,
        }

    @staticmethod
    def _reasoning(
        candidate_id: str, profile: dict[str, Any], signals: dict[str, Any],
        components: dict[str, float],
        requirements: list[dict[str, Any]], missing: list[str], services_only: bool,
        integrity: dict[str, Any], production_hits: list[str], relevant_product_roles: int,
    ) -> str:
        role = profile.get("current_title", "Candidate")
        company = profile.get("current_company", "their current company")
        years = float(profile.get("years_of_experience", 0) or 0)
        evidenced = [item for item in requirements if item["status"] != "missing"]
        strongest = max(evidenced, key=lambda item: item["score"], default=None)
        if strongest:
            strength = f"{strongest['requirement']} via {strongest['evidence']}"
        else:
            strength = "limited direct evidence for the core retrieval requirements"
        delivery = ", ".join(production_hits[:2]) if production_hits else "no explicit production marker"
        role_label = "role" if relevant_product_roles == 1 else "roles"
        templates = (
            f"{role} at {company} brings {years:g} years of experience. The clearest match is {strength}; "
            f"the record includes {relevant_product_roles} relevant product {role_label} and {delivery}.",
            f"For Redrob's ranking mandate, {strength} is the strongest evidence in this {years:g}-year profile. "
            f"{role} at {company} also shows {delivery} across {relevant_product_roles} relevant product {role_label}.",
            f"This profile connects {strength} with {delivery}. Its {years:g}-year path includes "
            f"{relevant_product_roles} relevant product {role_label}, currently as {role} at {company}.",
            f"The fit rests on {strength}, backed by {delivery}. {role} at {company} has {years:g} years overall "
            f"and {relevant_product_roles} relevant product {role_label}.",
            f"Across {relevant_product_roles} relevant product {role_label}, this candidate shows {strength} and "
            f"{delivery}. The current position is {role} at {company}, with {years:g} years total experience.",
        )
        template_index = sum(ord(character) for character in candidate_id) % len(templates)
        first = templates[template_index]

        response = round(float(signals.get("recruiter_response_rate", 0) or 0) * 100)
        notice = int(signals.get("notice_period_days", 0) or 0)
        last_active = str(signals.get("last_active_date", "unknown"))
        concerns = []
        if missing:
            concerns.append(f"missing evidence for {missing[0]}")
        if notice > 30:
            concerns.append(f"{notice}-day notice")
        if response < 25:
            concerns.append(f"{response}% recruiter response rate")
        if services_only:
            concerns.append("services-only career history")
        if integrity.get("flags"):
            concerns.append(integrity["flags"][0]["evidence"])
        if response >= 60 and signals.get("open_to_work_flag"):
            second = f"Recruiting viability is strong: {response}% response, open to work, last active {last_active}"
        elif response < 25:
            second = f"Recruiting risk needs attention: {response}% response, not marked open to work, last active {last_active}"
        elif not signals.get("open_to_work_flag"):
            second = f"Availability is mixed: {response}% response, not marked open to work, last active {last_active}"
        else:
            second = f"Availability is mixed: {response}% response and last active {last_active}"
        concern_text = ", ".join(item.rstrip(". ") for item in concerns[:2])
        second += "; " + ("primary concerns: " + concern_text if concerns else "no major concern detected") + "."
        return f"{first} {second}"

    @staticmethod
    def _questions(
        profile: dict[str, Any], requirements: list[dict[str, Any]], missing: list[str]
    ) -> list[str]:
        role = profile.get("current_title", "your current role")
        evidenced = next((item for item in requirements if item["status"] != "missing"), None)
        questions = []
        if evidenced:
            questions.append(
                f"In your work as {role}, describe the production architecture behind your {evidenced['requirement'].lower()} experience and how you measured quality regressions."
            )
        if missing:
            questions.append(
                f"Your profile does not evidence {missing[0].lower()}. What adjacent work best demonstrates that capability?"
            )
        else:
            questions.append("Walk through one ranking failure you diagnosed and the offline and online metrics you used to fix it.")
        questions.append(
            "What would you ship in the first two weeks if a BM25 candidate search worked but recruiter engagement was falling?"
        )
        return questions[:3]


class RankingService:
    def __init__(self, repository: CandidateRepository, scorer: CandidateScorer):
        self.repository = repository
        self.scorer = scorer

    def run(
        self, job: dict[str, Any], scope: str, limit: int = 100,
        max_candidates: int | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        semantic_active = self.scorer.prepare_job(job)
        heap: list[tuple[float, str, dict[str, Any]]] = []
        flagged: list[dict[str, Any]] = []
        integrity_severities: Counter[str] = Counter()
        integrity_reasons: Counter[str] = Counter()
        integrity_risk_bands: Counter[str] = Counter()
        processed = passed_integrity = relevance_pool = behaviorally_available = 0

        for candidate in self.repository.iter_candidates(scope, max_candidates):
            processed += 1
            evaluation = self.scorer.evaluate(candidate, job)
            if evaluation["disqualified"]:
                risk = evaluation["integrity"]["risk_score"]
                risk_band = "Critical (80-100%)" if risk >= 0.8 else "High (60-79%)"
                integrity_risk_bands[risk_band] += 1
                for flag in evaluation["integrity"]["flags"]:
                    integrity_severities[flag["severity"].capitalize()] += 1
                    integrity_reasons[self._integrity_category(flag["evidence"])] += 1
                if len(flagged) < 1_000:
                    flagged.append({
                        "candidate_id": evaluation["candidate_id"],
                        "name": evaluation["name"],
                        "role": evaluation["role"],
                        "risk_score": evaluation["integrity"]["risk_score"],
                        "flags": evaluation["integrity"]["flags"],
                    })
                continue
            passed_integrity += 1
            if evaluation["raw_fit"] >= 34:
                relevance_pool += 1
            if evaluation["behavioral"]["quality"] >= 0.50:
                behaviorally_available += 1
            key = (evaluation["score"], evaluation["candidate_id"])
            entry = (key[0], key[1], evaluation)
            if len(heap) < limit:
                heapq.heappush(heap, entry)
            elif key > (heap[0][0], heap[0][1]):
                heapq.heapreplace(heap, entry)

        results = [entry[2] for entry in heap]
        results.sort(key=lambda item: (-item["score"], item["candidate_id"]))
        for index, item in enumerate(results, 1):
            item["rank"] = index
            item["status"] = "Shortlisted" if index <= 10 else "Interview" if index <= 30 else "Screened"
            self.repository.remember({
                "candidate_id": item["candidate_id"], "profile": item["profile"],
                "career_history": item["career_history"], "skills": item["skills"],
                "redrob_signals": item["redrob_signals"], "education": [],
            })

        duration = time.perf_counter() - started
        metrics = self._metrics(
            results, flagged, processed, passed_integrity, relevance_pool,
            behaviorally_available, integrity_severities, integrity_reasons,
            integrity_risk_bands, job,
        )
        metrics["semantic_retrieval"] = {
            "active": semantic_active,
            "status": self.scorer.semantic.status() if self.scorer.semantic else {
                "enabled": False, "available": False, "active": False,
            },
        }
        return {
            "processed_count": processed,
            "duration_seconds": round(duration, 3),
            "results": results,
            "metrics": metrics,
        }

    @staticmethod
    def _integrity_category(evidence: str) -> str:
        lowered = evidence.lower()
        if "marked expert" in lowered:
            return "Impossible expert-duration claim"
        if "ai-heavy" in lowered or "listed skills" in lowered:
            return "Unsupported skill inventory"
        if "ends before" in lowered or "dates imply" in lowered:
            return "Temporal contradiction"
        if "declared experience" in lowered:
            return "Experience-history mismatch"
        if "profile declares" in lowered:
            return "Experience claim contradiction"
        return "Other integrity risk"

    @staticmethod
    def _metrics(
        results: list[dict[str, Any]], flagged: list[dict[str, Any]], processed: int,
        passed_integrity: int, relevance_pool: int, behaviorally_available: int,
        integrity_severities: Counter[str], integrity_reasons: Counter[str],
        integrity_risk_bands: Counter[str], job: dict[str, Any],
    ) -> dict[str, Any]:
        top10 = results[:10]
        avg_cph = round(sum(item["projected_cph_inr"] for item in top10) / max(1, len(top10)))
        avg_score = round(sum(item["score"] for item in results) / max(1, len(results)), 1)
        locations = Counter(item["location"] for item in results)
        score_bands = Counter(
            "90–100" if item["score"] >= 90 else "75–89" if item["score"] >= 75
            else "60–74" if item["score"] >= 60 else "Below 60"
            for item in results
        )
        component_max = results[0]["component_max"] if results else {}
        component_averages = [
            {
                "name": name.replace("_", " ").title(),
                "value": round(sum(item["components"][name] for item in results) / max(1, len(results)), 2),
                "maximum": maximum,
                "percent": round(
                    sum(item["components"][name] for item in results)
                    / max(1, len(results)) / maximum * 100, 1
                ),
            }
            for name, maximum in component_max.items()
        ]
        experience_min = float(job.get("parsed", {}).get("experience_min", 5))
        experience_max = float(job.get("parsed", {}).get("experience_max", 9))
        experience_bands = Counter(
            f"Below {experience_min:g} yrs" if item["years_experience"] < experience_min
            else f"Target {experience_min:g}-{experience_max:g} yrs"
            if item["years_experience"] <= experience_max
            else f"Above {experience_max:g} yrs"
            for item in results
        )
        notice_bands = Counter(
            "0-30 days" if item["notice_period_days"] <= 30 else
            "31-60 days" if item["notice_period_days"] <= 60 else
            "61-90 days" if item["notice_period_days"] <= 90 else "90+ days"
            for item in results
        )
        cph_bands = Counter(
            "Below ₹80K" if item["projected_cph_inr"] < 80_000 else
            "₹80K-₹1.1L" if item["projected_cph_inr"] <= 110_000 else
            "₹1.1L-₹1.5L" if item["projected_cph_inr"] <= 150_000 else "Above ₹1.5L"
            for item in results
        )
        salary_min = float(job.get("salary_min_lpa", 0) or 0)
        salary_max = float(job.get("salary_max_lpa", 0) or 0)
        salary_overlap = sum(
            float(item["salary_range_lpa"].get("min", 0) or 0) <= salary_max
            and float(item["salary_range_lpa"].get("max", 0) or 0) >= salary_min
            for item in results
        )
        requirement_names = list(dict.fromkeys(
            match["requirement"] for item in results for match in item["matched_requirements"]
        ))
        requirement_coverage = []
        for requirement in requirement_names:
            statuses = Counter(
                next(
                    match["status"] for match in item["matched_requirements"]
                    if match["requirement"] == requirement
                )
                for item in results
            )
            covered = statuses["exact"] + statuses["semantic"]
            requirement_coverage.append({
                "name": requirement,
                "exact": statuses["exact"],
                "semantic": statuses["semantic"],
                "missing": statuses["missing"],
                "coverage": round(covered / max(1, len(results)) * 100, 1),
            })
        known_offer_rates = [
            item["behavioral"]["offer_acceptance_rate"] for item in results
            if item["behavioral"]["offer_acceptance_rate"] is not None
        ]
        reasonings = [item["reasoning"].strip() for item in results]
        services_count = sum(bool(item["services_only"]) for item in results)
        return {
            "pipeline": [
                {"stage": "Loaded", "count": processed},
                {"stage": "Passed integrity", "count": passed_integrity},
                {"stage": "Relevance pool", "count": relevance_pool},
                {"stage": "Behaviorally available", "count": behaviorally_available},
                {"stage": "Final shortlist", "count": len(results)},
            ],
            "average_score": avg_score,
            "average_top10_cph_inr": avg_cph,
            "cph_benchmark_inr": 110_000,
            "top10_savings_inr": max(0, (110_000 - avg_cph) * len(top10)),
            "integrity_flags_count": processed - passed_integrity,
            "flagged": sorted(flagged, key=lambda item: -item["risk_score"]),
            "integrity_removal_rate": round((processed - passed_integrity) / max(1, processed) * 100, 3),
            "integrity_severity_distribution": [
                {"name": name, "value": value} for name, value in integrity_severities.most_common()
            ],
            "integrity_reason_distribution": [
                {"name": name, "value": value} for name, value in integrity_reasons.most_common()
            ],
            "integrity_risk_distribution": [
                {"name": name, "value": value} for name, value in integrity_risk_bands.items()
            ],
            "location_distribution": [
                {"name": name, "value": count} for name, count in locations.most_common(8)
            ],
            "score_distribution": [
                {"name": name, "value": score_bands.get(name, 0)}
                for name in ("90–100", "75–89", "60–74", "Below 60")
            ],
            "open_to_work_rate": round(
                sum(item["open_to_work"] for item in results) / max(1, len(results)) * 100, 1
            ),
            "average_response_rate": round(
                sum(item["response_rate"] for item in results) / max(1, len(results)) * 100, 1
            ),
            "average_availability_score": round(
                sum(item["behavioral"]["availability_score"] for item in results)
                / max(1, len(results)), 1
            ),
            "average_interview_show_rate": round(
                sum(item["behavioral"]["interview_show_rate"] for item in results)
                / max(1, len(results)), 1
            ),
            "average_offer_acceptance_rate": round(
                sum(known_offer_rates) / max(1, len(known_offer_rates)), 1
            ),
            "known_offer_history_rate": round(len(known_offer_rates) / max(1, len(results)) * 100, 1),
            "average_notice_period_days": round(
                sum(item["notice_period_days"] for item in results) / max(1, len(results)), 1
            ),
            "component_averages": component_averages,
            "experience_distribution": [
                {"name": name, "value": value} for name, value in experience_bands.items()
            ],
            "notice_distribution": [
                {"name": name, "value": notice_bands.get(name, 0)}
                for name in ("0-30 days", "31-60 days", "61-90 days", "90+ days")
            ],
            "cph_distribution": [
                {"name": name, "value": cph_bands.get(name, 0)}
                for name in ("Below ₹80K", "₹80K-₹1.1L", "₹1.1L-₹1.5L", "Above ₹1.5L")
            ],
            "average_shortlist_cph_inr": round(
                sum(item["projected_cph_inr"] for item in results) / max(1, len(results))
            ),
            "salary_overlap_rate": round(salary_overlap / max(1, len(results)) * 100, 1),
            "requirement_coverage": requirement_coverage,
            "company_background": [
                {"name": "Product / non-services", "value": len(results) - services_count},
                {"name": "Services-only", "value": services_count},
            ],
            "reasoning_quality": {
                "non_empty_rate": round(sum(bool(item) for item in reasonings) / max(1, len(reasonings)) * 100, 1),
                "unique_rate": round(len(set(reasonings)) / max(1, len(reasonings)) * 100, 1),
                "concern_coverage_rate": round(
                    sum("concern" in item.lower() for item in reasonings)
                    / max(1, len(reasonings)) * 100, 1
                ),
                "source": "Deterministic score-derived reasoning; no runtime LLM",
            },
            "top_candidate": {
                "candidate_id": results[0]["candidate_id"] if results else None,
                "name": results[0]["name"] if results else None,
                "score": results[0]["score"] if results else 0,
                "projected_cph_inr": results[0]["projected_cph_inr"] if results else 0,
            },
        }

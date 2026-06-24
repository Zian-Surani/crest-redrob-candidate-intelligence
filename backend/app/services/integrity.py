from __future__ import annotations

import re
from datetime import date
from typing import Any


AI_TERMS = (
    "embedding", "faiss", "pinecone", "weaviate", "qdrant", "milvus", "nlp", "llm",
    "retrieval", "ranking", "recommendation", "fine-tuning", "lora", "machine learning"
)
AI_ROLE_TERMS = ("ai ", "ml ", "machine learning", "data scientist", "nlp", "search", "recommend")


def _months_between(start: str, end: str | None) -> int | None:
    try:
        first = date.fromisoformat(start)
        last = date.today() if not end else date.fromisoformat(end)
    except (TypeError, ValueError):
        return None
    return (last.year - first.year) * 12 + last.month - first.month


def analyze_integrity(candidate: dict[str, Any]) -> dict[str, Any]:
    flags: list[dict[str, str]] = []
    risk = 0.0
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    impossible_skill = next(
        (
            skill for skill in skills
            if str(skill.get("proficiency", "")).lower() == "expert"
            and int(skill.get("duration_months", 0) or 0) <= 1
        ),
        None,
    )
    if impossible_skill:
        risk += 0.62
        flags.append({
            "severity": "critical",
            "evidence": f"{impossible_skill.get('name')} is marked expert with "
            f"{impossible_skill.get('duration_months', 0)} month(s) of use.",
        })

    career_months = 0
    for role in career:
        stated = int(role.get("duration_months", 0) or 0)
        calculated = _months_between(role.get("start_date", ""), role.get("end_date"))
        if calculated is not None and calculated < 0:
            risk += 0.9
            flags.append({
                "severity": "critical",
                "evidence": f"{role.get('company', 'A role')} ends before it starts.",
            })
        elif calculated is not None and abs(calculated - stated) > 10:
            risk += 0.38
            flags.append({
                "severity": "high",
                "evidence": f"{role.get('company', 'Role')} states {stated} months but dates imply {calculated}.",
            })
        career_months += max(stated, 0)

    declared_months = float(profile.get("years_of_experience", 0) or 0) * 12
    profile_claim_text = " ".join(
        str(profile.get(field, "")) for field in ("headline", "summary")
    ).lower()
    stated_years_match = re.search(
        r"\b(\d+(?:\.\d+)?)\+?\s+years?(?:\s+of)?(?:\s+hands-on)?\s+experience\b",
        profile_claim_text,
    )
    if stated_years_match and declared_months:
        stated_years = float(stated_years_match.group(1))
        career_years = career_months / 12 if career_months else 0
        declared_years = declared_months / 12
        if (
            abs(stated_years - declared_years) >= 2
            and career_years
            and abs(stated_years - career_years) <= 1.5
        ):
            risk += 0.62
            flags.append({
                "severity": "critical",
                "evidence": (
                    f"Profile declares {declared_years:g} years but states {stated_years:g} years "
                    f"and dated roles support about {career_years:.1f} years."
                ),
            })
    if career_months and abs(declared_months - career_months) > 42:
        risk += 0.32
        flags.append({
            "severity": "medium",
            "evidence": "Declared experience differs materially from dated career history.",
        })

    skill_text = " ".join(str(item.get("name", "")).lower() for item in skills)
    career_text = " ".join(
        f"{role.get('title', '')} {role.get('description', '')}" for role in career
    ).lower()
    ai_skill_count = sum(term in skill_text for term in AI_TERMS)
    career_evidence_count = sum(term in career_text for term in AI_TERMS)
    title = str(profile.get("current_title", "")).lower()
    if ai_skill_count >= 7 and career_evidence_count <= 1 and not any(term in title for term in AI_ROLE_TERMS):
        risk += 0.62
        flags.append({
            "severity": "critical",
            "evidence": "AI-heavy skill inventory is not supported by role titles or career descriptions.",
        })

    if len(skills) >= 28 and career_evidence_count <= 2:
        risk += 0.25
        flags.append({
            "severity": "medium",
            "evidence": f"{len(skills)} listed skills have limited corroborating career evidence.",
        })

    risk = min(risk, 1.0)
    # A single critical contradiction is sufficient to keep a profile out of the
    # shortlist. The 0.60 boundary was calibrated against the released pool:
    # it removes <1% of records while catching unsupported expert claims,
    # AI keyword stuffing, and large temporal inconsistencies.
    return {
        "risk_score": round(risk, 3),
        "passed": risk < 0.60,
        "flags": flags,
        "penalty": round(max(0.28, 1 - risk * 0.72), 3),
    }

import json
from pathlib import Path

import pytest

from app.services.integrity import analyze_integrity
from app.services.jd_parser import parse_job
from app.services.scoring import CandidateScorer, _skill_name_matches


def test_job_parser_finds_core_redrob_requirements():
    parsed = parse_job(
        "We absolutely need Python, production embeddings, vector search with FAISS, and NDCG evaluation. 5-9 years.",
        "Senior AI Engineer",
        "Pune, India",
    )
    assert parsed["experience_min"] == 5
    assert parsed["experience_max"] == 9
    assert "Python engineering" in parsed["required_skills"]
    assert "Ranking evaluation" in parsed["required_skills"]


def test_integrity_flags_impossible_expert_duration():
    candidate = {
        "profile": {"years_of_experience": 5, "current_title": "Marketing Manager"},
        "career_history": [{
            "company": "Example", "title": "Marketing Manager", "start_date": "2021-01-01",
            "end_date": None, "duration_months": 65, "description": "Campaign management"
        }],
        "skills": [{"name": "FAISS", "proficiency": "expert", "duration_months": 0}],
    }
    report = analyze_integrity(candidate)
    assert report["risk_score"] >= 0.6
    assert report["passed"] is False
    assert report["flags"]


def test_sample_candidate_scoring_is_deterministic():
    data_root = Path(__file__).resolve().parents[1] / "data"
    sample_path = next(
        path for path in data_root.rglob("sample_candidates.json") if "__MACOSX" not in path.parts
    )
    candidate = json.loads(sample_path.read_text(encoding="utf-8"))[0]
    description = "Senior AI Engineer. Need Python, embeddings, vector search, NDCG. 5-9 years. Pune, India."
    job = {
        "description": description, "title": "Senior AI Engineer", "location": "Pune, India",
        "salary_min_lpa": 25, "salary_max_lpa": 40,
        "parsed": parse_job(description, "Senior AI Engineer", "Pune, India"),
    }
    scorer = CandidateScorer()
    first = scorer.evaluate(candidate, job)
    second = scorer.evaluate(candidate, job)
    assert first["score"] == second["score"]
    assert 0 <= first["score"] <= 100
    assert first["reasoning"] == second["reasoning"]


def test_short_skill_name_does_not_collide_with_python_frameworks():
    assert _skill_name_matches("Go", ("python", "django", "pytorch")) is False
    assert _skill_name_matches("Python", ("python", "django", "pytorch")) is True


def test_integrity_rejects_declared_experience_contradiction():
    candidate = {
        "profile": {
            "years_of_experience": 2.9,
            "headline": "Senior ML Engineer",
            "summary": "Senior engineer with 6.3 years of hands-on experience.",
            "current_title": "Senior ML Engineer",
        },
        "career_history": [{
            "company": "Product Co", "title": "ML Engineer", "start_date": "2020-01-01",
            "end_date": None, "duration_months": 74, "description": "Shipped ranking systems",
        }],
        "skills": [],
    }
    report = analyze_integrity(candidate)
    assert report["passed"] is False
    assert any("Profile declares 2.9 years" in flag["evidence"] for flag in report["flags"])


def test_behavioral_multiplier_is_applied_to_final_score():
    data_root = Path(__file__).resolve().parents[1] / "data"
    sample_path = next(
        path for path in data_root.rglob("sample_candidates.json") if "__MACOSX" not in path.parts
    )
    candidate = json.loads(sample_path.read_text(encoding="utf-8"))[0]
    description = "Senior AI Engineer. Need Python, embeddings, vector search, NDCG. 5-9 years. Pune, India."
    job = {
        "description": description, "title": "Senior AI Engineer", "location": "Pune, India",
        "salary_min_lpa": 25, "salary_max_lpa": 40,
        "parsed": parse_job(description, "Senior AI Engineer", "Pune, India"),
    }
    result = CandidateScorer().evaluate(candidate, job)
    expected = result["raw_fit"] * result["behavioral"]["multiplier"] * result["integrity"]["penalty"]
    assert result["score"] == pytest.approx(expected, abs=0.002)

from app.audit import automated_relevance_tier, reasoning_checks


def sample_result() -> dict:
    return {
        "candidate_id": "CAND_TEST",
        "role": "Recommendation Engineer",
        "company": "Product Co",
        "years_experience": 6.0,
        "score": 88.0,
        "reasoning": (
            "Recommendation Engineer at Product Co brings 6 years of experience. "
            "The clearest match is Ranking evaluation via NDCG; primary concerns: 60-day notice."
        ),
        "profile": {"current_title": "Recommendation Engineer"},
        "behavioral": {"availability_score": 85},
        "career_evidence": {"relevant_product_role_count": 3},
        "matched_requirements": [
            {
                "requirement": "Ranking evaluation",
                "status": "exact",
                "score": 90,
                "evidence": "NDCG",
            }
            for _ in range(4)
        ],
        "missing_requirements": [],
        "notice_period_days": 60,
        "response_rate": 0.9,
        "open_to_work": True,
        "services_only": False,
        "disqualified": False,
    }


def test_automated_relevance_tier_rewards_complete_product_fit():
    tier, _ = automated_relevance_tier(
        sample_result(), {"parsed": {"experience_min": 5, "experience_max": 9}}
    )
    assert tier == 5


def test_reasoning_checks_grounded_specific_facts():
    checks = reasoning_checks(sample_result(), True)
    assert all(checks.values())

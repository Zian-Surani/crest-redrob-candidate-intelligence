from __future__ import annotations

from typing import Any


SCORING_METRICS = [
    {"name": "NDCG@10", "weight": 50, "purpose": "Quality and ordering of the top 10 candidates"},
    {"name": "NDCG@50", "weight": 30, "purpose": "Quality and ordering through rank 50"},
    {"name": "MAP", "weight": 15, "purpose": "Precision across all hidden relevance levels"},
    {"name": "P@10", "weight": 5, "purpose": "Fraction of top 10 candidates at relevance tier 3 or above"},
]

EVALUATION_STAGES = [
    {
        "stage": 1, "name": "Format validation",
        "checks": "Exactly 100 UTF-8 CSV rows, correct columns, ranks, IDs, and score order.",
        "elimination": "Any submission-format violation or missing working sandbox link.",
    },
    {
        "stage": 2, "name": "Hidden-ground-truth scoring",
        "checks": "0.50 NDCG@10 + 0.30 NDCG@50 + 0.15 MAP + 0.05 P@10.",
        "elimination": "Composite score below the advancement cutoff.",
    },
    {
        "stage": 3, "name": "Code reproduction and honeypot check",
        "checks": "Full repo reproduces within 5 minutes, 16 GB, CPU-only, network off.",
        "elimination": "Non-reproducible code, fabricated repo, or over 10% honeypots in top 100.",
    },
    {
        "stage": 4, "name": "Manual reasoning and methodology review",
        "checks": "Specific facts, JD connection, honest concerns, no hallucination, variation, rank consistency.",
        "elimination": "Weak reasoning, incoherent methodology, flat/inauthentic Git history, or LLM-only code.",
    },
    {
        "stage": 5, "name": "Defend-your-work interview",
        "checks": "Thirty-minute architecture walkthrough and technical defense.",
        "elimination": "Cannot explain the implementation or contradicts submitted code.",
    },
]

REASONING_CHECKS = [
    "Uses specific facts from the candidate profile",
    "Connects evidence to a named JD requirement",
    "States material gaps or concerns honestly",
    "Contains no unsupported skill, employer, or experience claim",
    "Varies substantively between candidates",
    "Uses a tone consistent with the candidate's rank",
]

SUBMISSION_REQUIREMENTS = [
    "CSV filename must be the registered participant ID with a .csv extension",
    "Exactly 100 rows with candidate_id, rank, score, reasoning in that order",
    "Ranks 1 through 100 and candidate IDs must each be unique",
    "Scores must be non-increasing and ties broken deterministically",
    "Ranking runtime at most 5 minutes, memory at most 16 GB, CPU only, network off",
    "GitHub repo with README, dependencies, full source, artifacts/scripts, and one reproduction command",
    "submission_metadata.yaml at repository root matching the portal metadata",
    "Working sandbox that ranks at most 100 uploaded or preloaded candidates and exports CSV",
    "Honest AI-tool declaration, compute summary, team details, and methodology summary",
    "Maximum three portal submissions; the last valid submission counts",
]

BEHAVIORAL_SIGNAL_GROUPS = [
    {
        "name": "Profile trust", "signals": [
            "profile_completeness_score", "verified_email", "verified_phone", "linkedin_connected"
        ]
    },
    {
        "name": "Market intent", "signals": [
            "last_active_date", "open_to_work_flag", "applications_submitted_30d",
            "preferred_work_mode", "willing_to_relocate"
        ]
    },
    {
        "name": "Recruiter engagement", "signals": [
            "recruiter_response_rate", "avg_response_time_hours", "profile_views_received_30d",
            "search_appearance_30d", "saved_by_recruiters_30d"
        ]
    },
    {
        "name": "Evidence and network", "signals": [
            "skill_assessment_scores", "connection_count", "endorsements_received",
            "github_activity_score"
        ]
    },
    {
        "name": "Hireability", "signals": [
            "notice_period_days", "expected_salary_range_inr_lpa",
            "interview_completion_rate", "offer_acceptance_rate"
        ]
    },
]


def challenge_requirements() -> dict[str, Any]:
    return {
        "deliverable": "Rank the best 100 candidates for the released Senior AI Engineer JD and explain every rank.",
        "scoring_metrics": SCORING_METRICS,
        "evaluation_stages": EVALUATION_STAGES,
        "reasoning_checks": REASONING_CHECKS,
        "submission_requirements": SUBMISSION_REQUIREMENTS,
        "behavioral_signal_groups": BEHAVIORAL_SIGNAL_GROUPS,
        "tiebreaks": ["Higher P@5", "Higher P@10", "Earlier submission timestamp"],
        "honeypot_rule": "Over 10% honeypots in the top 100 is a Stage 3 disqualification.",
    }

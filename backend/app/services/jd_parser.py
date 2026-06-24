from __future__ import annotations

import re
from typing import Any


SKILL_GROUPS: dict[str, tuple[str, ...]] = {
    "Embeddings & semantic retrieval": (
        "embedding", "semantic search", "dense retrieval", "sentence-transformer", "bge", "e5"
    ),
    "Vector & hybrid search": (
        "vector database", "vector search", "hybrid search", "faiss", "pinecone",
        "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch"
    ),
    "Python engineering": (
        "python", "fastapi", "flask", "django", "pytorch", "scikit-learn", "sklearn"
    ),
    "Ranking evaluation": (
        "ndcg", "mrr", "mean reciprocal rank", "map", "ranking evaluation",
        "offline evaluation", "a/b test", "ab test"
    ),
    "Learning to rank": ("learning to rank", "ltr", "lambdamart", "xgboost rank"),
    "LLM fine-tuning": ("fine-tuning", "finetuning", "lora", "qlora", "peft"),
    "NLP / information retrieval": (
        "nlp", "information retrieval", "search relevance", "recommendation system",
        "recommender system", "ranking system"
    ),
    "ML production systems": (
        "mlops", "model serving", "production ml", "inference", "feature store",
        "model monitoring", "ml pipeline"
    ),
    "Distributed systems": (
        "distributed systems", "kafka", "spark", "kubernetes", "large-scale", "high scale"
    ),
    "HR technology": ("hr tech", "hr-tech", "recruiting", "talent marketplace", "ats"),
}

CORE_DEFAULTS = [
    "Embeddings & semantic retrieval",
    "Vector & hybrid search",
    "Python engineering",
    "Ranking evaluation",
]


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def parse_job(description: str, title: str, location: str) -> dict[str, Any]:
    text = f"{title}\n{location}\n{description}".lower()
    detected = [name for name, terms in SKILL_GROUPS.items() if _contains_any(text, terms)]
    required: list[str] = []
    preferred: list[str] = []
    for name in detected:
        first_term = next((term for term in SKILL_GROUPS[name] if term in text), "")
        index = text.find(first_term)
        context = text[max(0, index - 120): index + 160]
        if any(marker in context for marker in ("must", "required", "absolutely", "need", "strong")):
            required.append(name)
        else:
            preferred.append(name)

    if "senior ai engineer" in text or "founding" in text:
        for skill in CORE_DEFAULTS:
            if skill not in required:
                required.append(skill)
            if skill in preferred:
                preferred.remove(skill)
    if not required:
        required = detected[:4] or ["Python engineering"]
        preferred = [skill for skill in detected if skill not in required]

    experience_patterns = [
        r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)",
        r"(?:minimum|min\.?|at least)\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)",
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)(?:\s+of)?\s+experience",
    ]
    experience_min, experience_max = 3.0, 12.0
    for pattern in experience_patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        experience_min = float(match.group(1))
        experience_max = float(match.group(2)) if match.lastindex and match.lastindex > 1 else experience_min + 5
        break

    known_locations = [
        "Pune", "Noida", "Delhi NCR", "Delhi", "Hyderabad", "Bengaluru", "Bangalore",
        "Mumbai", "Chennai", "Gurugram", "Gurgaon", "India", "Remote"
    ]
    locations = []
    for city in known_locations:
        if city.lower() in text and city not in locations:
            locations.append(city)
    if not locations:
        locations = [part.strip() for part in re.split(r"[,/]", location) if part.strip()]

    disqualifiers = []
    for marker, label in (
        ("pure research", "Research-only background without production deployment"),
        ("consulting firms", "Services-only career history"),
        ("computer vision", "Primary expertise outside NLP / IR"),
        ("hasn't written production code", "No recent hands-on production coding"),
    ):
        if marker in text:
            disqualifiers.append(label)

    return {
        "required_skills": required,
        "preferred_skills": preferred,
        "experience_min": experience_min,
        "experience_max": experience_max,
        "locations": locations,
        "country": "India" if "india" in text else "",
        "work_mode": "hybrid" if "hybrid" in text else "flexible",
        "notice_period_target": 30 if "30" in text and "notice" in text else 60,
        "disqualifiers": disqualifiers,
    }


def group_hits(text: str, group: str) -> list[str]:
    lowered = text.lower()
    return [term for term in SKILL_GROUPS.get(group, ()) if term in lowered]

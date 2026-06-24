from app.services.semantic import candidate_embedding_text


def test_embedding_text_is_bounded_and_contains_evidence():
    candidate = {
        "profile": {
            "headline": "Search engineer",
            "summary": "Built retrieval systems for real users.",
            "current_title": "ML Engineer",
            "current_industry": "Software",
        },
        "career_history": [{
            "title": "ML Engineer", "industry": "Software",
            "description": "Deployed hybrid search and measured NDCG in production."
        }],
        "skills": [{"name": "FAISS"}, {"name": "Python"}],
    }
    text = candidate_embedding_text(candidate)
    assert len(text) <= 2_400
    assert "hybrid search" in text
    assert "FAISS" in text

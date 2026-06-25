from __future__ import annotations

import argparse
import csv
from pathlib import Path

from docx import Document

from app.config import settings
from app.repository import CandidateRepository
from app.services.jd_parser import parse_job
from app.services.scoring import CandidateScorer, RankingService
from app.services.semantic import SemanticScorer
from app.store import Store


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reproducible CREST candidate ranker.")
    parser.add_argument("--scope", choices=("sample", "full"), default="full")
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--candidates", help="Path to candidates.jsonl")
    parser.add_argument("--job-description", help="Path to the released .docx or a text JD")
    parser.add_argument("--artifact-dir", help="Path to precomputed semantic artifacts")
    parser.add_argument("--output", "--out", dest="output", default="crest_submission.csv")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist this run to the local SQLite store for Analytics/Pipeline pages.",
    )
    args = parser.parse_args()

    candidate_path = Path(args.candidates).resolve() if args.candidates else None
    jd_path = Path(args.job_description).resolve() if args.job_description else None
    repository = CandidateRepository(
        candidate_path.parent if candidate_path else settings.data_dir,
        full_path=candidate_path, default_jd_path=jd_path,
    )
    selected_jd = jd_path or repository.default_jd_path
    if selected_jd.suffix.lower() == ".docx":
        description = "\n".join(
            paragraph.text.strip()
            for paragraph in Document(selected_jd).paragraphs
            if paragraph.text.strip()
        )
    else:
        description = selected_jd.read_text(encoding="utf-8")
    job = {
        "title": "Senior AI Engineer — Founding Team", "company": "Redrob AI",
        "location": "Pune / Noida, India", "description": description,
        "salary_min_lpa": 25, "salary_max_lpa": 40,
        "parsed": parse_job(description, "Senior AI Engineer — Founding Team", "Pune / Noida, India"),
    }
    semantic = SemanticScorer(
        Path(args.artifact_dir).resolve() if args.artifact_dir else settings.semantic_artifact_dir,
        settings.semantic_model, settings.semantic_enabled,
    )
    outcome = RankingService(repository, CandidateScorer(semantic)).run(
        job, args.scope, 100, args.max_candidates
    )
    output = Path(args.output)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for item in outcome["results"]:
            writer.writerow([item["candidate_id"], item["rank"], f"{item['normalized_score']:.6f}", item["reasoning"]])
    ranking_id = None
    if args.persist:
        store = Store(settings.database_path)
        store.initialize()
        persisted_job = store.create_job(job)
        ranking = store.save_ranking({
            "job_id": persisted_job["id"],
            "scope": args.scope,
            **outcome,
        })
        ranking_id = ranking["id"]
    print(
        f"Wrote {len(outcome['results'])} rows to {output.resolve()} after scoring "
        f"{outcome['processed_count']} candidates in {outcome['duration_seconds']}s."
        + (f" Persisted ranking_id={ranking_id}." if ranking_id else "")
    )


if __name__ == "__main__":
    main()

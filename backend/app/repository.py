from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator


class DatasetNotFoundError(RuntimeError):
    pass


class CandidateRepository:
    """Locates and streams the official challenge data without loading 487 MB into RAM."""

    def __init__(
        self, data_dir: Path, full_path: Path | None = None,
        sample_path: Path | None = None, default_jd_path: Path | None = None,
    ):
        self.data_dir = data_dir
        self._full_override = full_path
        self._sample_override = sample_path
        self._jd_override = default_jd_path
        self._candidate_cache: dict[str, dict[str, Any]] = {}

    @cached_property
    def full_path(self) -> Path:
        if self._full_override:
            return self._full_override
        matches = [
            path
            for path in self.data_dir.rglob("candidates.jsonl")
            if "__MACOSX" not in path.parts
        ]
        if not matches:
            raise DatasetNotFoundError(
                f"candidates.jsonl was not found below {self.data_dir}. "
                "Extract the official Redrob challenge bundle into backend/data."
            )
        return max(matches, key=lambda item: item.stat().st_size)

    @cached_property
    def sample_path(self) -> Path:
        if self._sample_override:
            return self._sample_override
        matches = [
            path
            for path in self.data_dir.rglob("sample_candidates.json")
            if "__MACOSX" not in path.parts
        ]
        if not matches:
            raise DatasetNotFoundError(
                f"sample_candidates.json was not found below {self.data_dir}."
            )
        return matches[0]

    @cached_property
    def default_jd_path(self) -> Path:
        if self._jd_override:
            return self._jd_override
        matches = [
            path
            for path in self.data_dir.rglob("job_description.docx")
            if "__MACOSX" not in path.parts
        ]
        if not matches:
            raise DatasetNotFoundError(
                f"job_description.docx was not found below {self.data_dir}."
            )
        return matches[0]

    def iter_candidates(
        self, scope: str = "full", max_candidates: int | None = None
    ) -> Iterator[dict[str, Any]]:
        emitted = 0
        if scope == "sample":
            records = json.loads(self.sample_path.read_text(encoding="utf-8"))
            for candidate in records:
                self.remember(candidate)
                yield candidate
                emitted += 1
                if max_candidates and emitted >= max_candidates:
                    return
            return

        with self.full_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                candidate = json.loads(line)
                yield candidate
                emitted += 1
                if max_candidates and emitted >= max_candidates:
                    return

    def remember(self, candidate: dict[str, Any]) -> None:
        candidate_id = candidate.get("candidate_id")
        if candidate_id:
            self._candidate_cache[candidate_id] = candidate

    def remember_many(self, candidates: list[dict[str, Any]]) -> None:
        for candidate in candidates:
            self.remember(candidate)

    def get_candidate(self, candidate_id: str) -> dict[str, Any] | None:
        cached = self._candidate_cache.get(candidate_id)
        if cached:
            return cached

        for candidate in self.iter_candidates("sample"):
            if candidate.get("candidate_id") == candidate_id:
                return candidate

        for candidate in self.iter_candidates("full"):
            if candidate.get("candidate_id") == candidate_id:
                self.remember(candidate)
                return candidate
        return None

    def stats(self) -> dict[str, Any]:
        full_available = False
        full_size = 0
        try:
            full_size = self.full_path.stat().st_size
            full_available = True
        except DatasetNotFoundError:
            pass
        sample_count = sum(1 for _ in self.iter_candidates("sample"))
        return {
            "name": "Redrob India Data & AI Challenge",
            "full_available": full_available,
            "candidate_count": 100_000 if full_available else sample_count,
            "sample_count": sample_count,
            "full_size_bytes": full_size,
            "format": "JSONL",
            "streaming": True,
            "behavioral_signals": 23,
        }

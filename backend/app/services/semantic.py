from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def candidate_embedding_text(candidate: dict[str, Any]) -> str:
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    sections = [
        str(profile.get("headline", "")),
        str(profile.get("summary", "")),
        str(profile.get("current_title", "")),
        str(profile.get("current_industry", "")),
        " ".join(
            f"{role.get('title', '')}. {role.get('industry', '')}. {role.get('description', '')}"
            for role in career
        ),
        "Skills: " + ", ".join(str(skill.get("name", "")) for skill in skills),
    ]
    # Keep the representation bounded so long, keyword-stuffed profiles cannot
    # dominate the vector and CPU precomputation stays practical.
    return "\n".join(section.strip() for section in sections if section.strip())[:2_400]


class SemanticScorer:
    """Loads offline MiniLM artifacts and provides network-free cosine similarity."""

    def __init__(self, artifact_dir: Path, model_name: str, enabled: bool = True):
        self.artifact_dir = artifact_dir
        self.model_name = model_name
        self.enabled = enabled
        self.embeddings_path = artifact_dir / "candidate_embeddings.npy"
        self.ids_path = artifact_dir / "candidate_ids.txt"
        self.metadata_path = artifact_dir / "metadata.json"
        self.bulk_similarity = os.getenv(
            "CREST_SEMANTIC_BULK_SIMILARITY", "true"
        ).strip().lower() in {"1", "true", "yes", "on"}
        self._embeddings = None
        self._id_to_index: dict[str, int] | None = None
        self._model = None
        self._job_vector = None
        self._similarities = None
        self._job_hash = ""
        self._error = ""

    @property
    def artifact_available(self) -> bool:
        return all(path.exists() for path in (
            self.embeddings_path, self.ids_path, self.metadata_path,
        ))

    def status(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.metadata_path.exists():
            try:
                metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metadata = {}
        return {
            "enabled": self.enabled,
            "available": self.artifact_available,
            "active": self._job_vector is not None,
            "model": metadata.get("model", self.model_name),
            "candidate_count": metadata.get("candidate_count", 0),
            "dimension": metadata.get("dimension", 0),
            "max_seq_length": metadata.get("max_seq_length", 0),
            "bulk_similarity": self.bulk_similarity,
            "precomputed_similarity_count": int(len(self._similarities))
            if self._similarities is not None else 0,
            "artifact_dir": str(self.artifact_dir),
            "network_required_during_ranking": False,
            "error": self._error,
        }

    def _load(self) -> bool:
        if not self.enabled or not self.artifact_available:
            return False
        if self._embeddings is not None:
            return True
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            self._embeddings = np.load(self.embeddings_path, mmap_mode="r")
            ids = [line.strip() for line in self.ids_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(ids) != len(self._embeddings):
                raise ValueError("Embedding row count does not match candidate ID count")
            self._id_to_index = {candidate_id: index for index, candidate_id in enumerate(ids)}
            self._model = SentenceTransformer(self.model_name, local_files_only=True, device="cpu")
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            self._model.max_seq_length = int(metadata.get("max_seq_length", 128))
            self._error = ""
            return True
        except Exception as exc:  # graceful fallback keeps the ranker reproducible
            self._error = str(exc)
            self._embeddings = None
            self._id_to_index = None
            self._model = None
            self._similarities = None
            return False

    def prepare_job(self, description: str) -> bool:
        if not self._load():
            self._job_vector = None
            self._similarities = None
            return False
        digest = hashlib.sha256(description.encode("utf-8")).hexdigest()
        if (
            digest == self._job_hash
            and self._job_vector is not None
            and self._similarities is not None
        ):
            return True
        vector = self._model.encode(
            [description], normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        )[0]
        self._job_vector = vector
        self._job_hash = digest
        try:
            import numpy as np

            if self.bulk_similarity:
                similarities = self._embeddings @ vector.astype("float32")
                self._similarities = np.clip(
                    np.asarray(similarities, dtype="float32"), 0.0, 1.0
                )
            else:
                self._similarities = None
        except Exception as exc:
            self._error = f"semantic vector pre-score failed: {exc}"
            self._similarities = None
        return True

    def similarity(self, candidate_id: str) -> float | None:
        if self._job_vector is None or self._embeddings is None or self._id_to_index is None:
            return None
        index = self._id_to_index.get(candidate_id)
        if index is None:
            return None
        if self._similarities is not None:
            return float(self._similarities[index])
        import numpy as np
        similarity = float(np.dot(self._embeddings[index].astype("float32"), self._job_vector))
        return min(1.0, max(0.0, similarity))

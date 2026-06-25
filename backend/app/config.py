from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "CREST API"
    api_prefix: str = "/api"
    data_dir: Path = Path(os.getenv("CREST_DATA_DIR", str(BACKEND_DIR / "data")))
    database_path: Path = Path(
        os.getenv("CREST_DATABASE_PATH", str(BACKEND_DIR / "data" / "crest.db"))
    )
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "CREST_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    )
    token_secret: str = os.getenv("CREST_TOKEN_SECRET", "local-development-secret-change-me")
    token_ttl_seconds: int = int(os.getenv("CREST_TOKEN_TTL_SECONDS", "86400"))
    bootstrap_demo: bool = _bool_env("CREST_BOOTSTRAP_DEMO", False)
    ollama_enabled: bool = _bool_env("CREST_OLLAMA_ENABLED", True)
    ollama_url: str = os.getenv("CREST_OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("CREST_OLLAMA_MODEL", "qwen2.5-coder:7b")
    ollama_fast_model: str = os.getenv("CREST_OLLAMA_FAST_MODEL", "qwen2.5-coder:7b")
    ollama_deep_model: str = os.getenv("CREST_OLLAMA_DEEP_MODEL", "qwen2.5-coder:14b")
    semantic_enabled: bool = _bool_env("CREST_SEMANTIC_ENABLED", True)
    semantic_model: str = os.getenv(
        "CREST_SEMANTIC_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    semantic_artifact_dir: Path = Path(
        os.getenv("CREST_SEMANTIC_ARTIFACT_DIR", str(BACKEND_DIR / "data" / "embeddings"))
    )
    frontend_dist: Path = Path(
        os.getenv("CREST_FRONTEND_DIST", str(BACKEND_DIR.parent / "frontend" / "dist"))
    )
    sandbox_url: str = os.getenv("CREST_SANDBOX_URL", "")


settings = Settings()

"""Repository-root reproduction entrypoint required by the challenge handoff."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from app.cli import main  # noqa: E402


if __name__ == "__main__":
    main()

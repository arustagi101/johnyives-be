from __future__ import annotations

from pathlib import Path

BASE_RUNTIME = Path("./runtime").resolve()


def create_job_dir(kind: str, job_id: str) -> str:
    path = BASE_RUNTIME / kind / job_id
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

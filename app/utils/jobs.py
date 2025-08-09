from __future__ import annotations

from threading import RLock
import logging
from typing import Any, Dict, Optional


logger = logging.getLogger("ych.jobs")


class _Jobs:
    def __init__(self) -> None:
        self._lock = RLock()
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {
            "audit": {},
            "generate": {},
        }

    def create_job(self, kind: str, job_id: str) -> None:
        with self._lock:
            self._store[kind][job_id] = {"status": "queued", "result": None, "error": None}
        logger.info("job.create | %s:%s", kind, job_id)

    def complete_job(self, kind: str, job_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            job = self._store[kind].get(job_id)
            if job is not None:
                job["status"] = "done"
                job["result"] = result
                job["error"] = None
        logger.info("job.done | %s:%s", kind, job_id)

    def fail_job(self, kind: str, job_id: str, error: Dict[str, Any]) -> None:
        with self._lock:
            job = self._store[kind].get(job_id)
            if job is not None:
                job["status"] = "error"
                job["error"] = error
        logger.info("job.error | %s:%s | %s", kind, job_id, (error or {}).get("error"))

    def get_job(self, kind: str, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._store.get(kind, {}).get(job_id)
            return dict(job) if job is not None else None


jobs = _Jobs()

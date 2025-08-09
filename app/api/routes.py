import logging
import traceback
from uuid import uuid4
from typing import Any
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.schemas import (
    AuditRequest,
    AuditStatusResponse,
    GenerateRequest,
    GenerateStatusResponse,
)
from app.utils.jobs import jobs
from app.utils.storage import create_job_dir
from app.services.audit import perform_audit
from app.services.generator import generate_nextjs_project
from app.services.pipeline import run_full_generation

logger = logging.getLogger("ych.api")
router = APIRouter()


@router.post("/audit", response_model=dict)
async def start_audit(req: AuditRequest, bg: BackgroundTasks) -> dict:
    audit_id = str(uuid4())
    jobs.create_job("audit", audit_id)
    logger.info("[audit:%s] queued | url=%s", audit_id, req.url)

    def _run() -> None:
        try:
            out_dir = create_job_dir("audit", audit_id)
            logger.info("[audit:%s] started | out_dir=%s", audit_id, out_dir)
            result = perform_audit(req.url, req.options or {}, out_dir)
            jobs.complete_job("audit", audit_id, result)
            logger.info("[audit:%s] completed | screenshots=%s", audit_id, len(result.get("artifacts", {}).get("screenshots", [])))
        except Exception as exc:  # noqa: BLE001
            jobs.fail_job("audit", audit_id, {
                "error": str(exc),
                "traceback": traceback.format_exc(),
            })
            logger.exception("[audit:%s] failed: %s", audit_id, exc)

    bg.add_task(_run)
    return {"audit_id": audit_id}


@router.get("/audit/{audit_id}", response_model=AuditStatusResponse)
async def get_audit(audit_id: str) -> AuditStatusResponse:
    job = jobs.get_job("audit", audit_id)
    if not job:
        raise HTTPException(status_code=404, detail="audit not found")
    logger.info("[audit:%s] polled | status=%s", audit_id, job.get("status"))
    return AuditStatusResponse(**job)


@router.post("/generate", response_model=dict)
async def start_generate(req: GenerateRequest, bg: BackgroundTasks) -> dict:
    # Accept either a completed audit_id, or content provided directly
    audit_result: dict[str, Any] = {}
    from_audit = False
    if req.audit_id:
        audit_job = jobs.get_job("audit", req.audit_id)
        if not audit_job or audit_job.get("status") != "done":
            raise HTTPException(status_code=400, detail="audit not found or incomplete")
        audit_result = audit_job.get("result", {})
        from_audit = True
    elif not req.content:
        raise HTTPException(status_code=400, detail="must provide content or a completed audit_id")

    gen_id = str(uuid4())
    jobs.create_job("generate", gen_id)
    logger.info("[generate:%s] queued | from_audit=%s", gen_id, from_audit)

    def _run() -> None:
        try:
            out_dir = create_job_dir("generate", gen_id)
            logger.info("[generate:%s] started | out_dir=%s", gen_id, out_dir)
            result = run_full_generation(
                audit_results=audit_result,
                out_dir=out_dir,
                tone=req.tone or ((req.preferences or {}).get("tone") if req.preferences else "professional"),
                criteria=None,
                content=req.content,
            )
            jobs.complete_job("generate", gen_id, result)
            logger.info("[generate:%s] completed | project_dir=%s", gen_id, result.get("project_dir"))
        except Exception as exc:  # noqa: BLE001
            jobs.fail_job("generate", gen_id, {
                "error": str(exc),
                "traceback": traceback.format_exc(),
            })
            logger.exception("[generate:%s] failed: %s", gen_id, exc)

    bg.add_task(_run)
    return {"job_id": gen_id}


@router.get("/generate/{job_id}", response_model=GenerateStatusResponse)
async def get_generate(job_id: str) -> GenerateStatusResponse:
    job = jobs.get_job("generate", job_id)
    if not job:
        raise HTTPException(status_code=404, detail="generation job not found")
    logger.info("[generate:%s] polled | status=%s", job_id, job.get("status"))
    return GenerateStatusResponse(**job)

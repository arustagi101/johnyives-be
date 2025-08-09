import time
from pathlib import Path
import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app


logger = logging.getLogger("ych.test")

def test_e2e_audit_and_generate_wholebodysj():
    logger.info("e2e.start")
    client = TestClient(app)

    # 1) Start audit
    resp = client.post("/audit", json={"url": "https://www.wholebodysj.com/"})
    assert resp.status_code == 200, resp.text
    audit_id = resp.json()["audit_id"]
    logger.info("e2e.audit.queued | audit_id=%s", audit_id)

    # 2) Poll audit until done
    deadline = time.time() + 180
    audit_result = None
    while time.time() < deadline:
        r = client.get(f"/audit/{audit_id}")
        assert r.status_code == 200, r.text
        payload = r.json()
        if payload["status"] == "done":
            audit_result = payload["result"]
            logger.info(
                "e2e.audit.done | screenshots=%s",
                len(audit_result.get("artifacts", {}).get("screenshots", [])),
            )
            break
        if payload["status"] == "error":
            pytest.fail(f"audit error: {payload.get('error')}")
        logger.info("e2e.audit.poll | status=%s", payload["status"])
        time.sleep(3)

    assert audit_result is not None, "audit did not complete in time"

    # Validate basic artifacts
    artifacts = audit_result.get("artifacts", {})
    screenshots = artifacts.get("screenshots", [])
    assert screenshots, "expected at least one screenshot"
    for p in screenshots[:2]:
        assert Path(p).exists(), f"screenshot not found: {p}"

    # 3) Start generation
    logger.info("e2e.generate.start | audit_id=%s", audit_id)
    resp = client.post("/generate", json={"audit_id": audit_id})
    assert resp.status_code == 200, resp.text
    gen_id = resp.json()["job_id"]
    logger.info("e2e.generate.queued | job_id=%s", gen_id)

    # 4) Poll generation until done
    deadline = time.time() + 180
    gen_result = None
    while time.time() < deadline:
        r = client.get(f"/generate/{gen_id}")
        assert r.status_code == 200, r.text
        payload = r.json()
        if payload["status"] == "done":
            gen_result = payload["result"]
            logger.info("e2e.generate.done | project_dir=%s", gen_result.get("project_dir"))
            break
        if payload["status"] == "error":
            pytest.fail(f"generation error: {payload.get('error')}")
        logger.info("e2e.generate.poll | status=%s", payload["status"])
        time.sleep(2)

    assert gen_result is not None, "generation did not complete in time"

    zip_path = gen_result.get("zip_path")
    project_dir = gen_result.get("project_dir")
    assert zip_path and Path(zip_path).exists(), f"missing zip at {zip_path}"
    assert project_dir and Path(project_dir).exists(), f"missing project dir at {project_dir}"

    # Ensure analysis.json exists in generated project for traceability
    analysis_path = Path(project_dir) / "analysis.json"
    assert analysis_path.exists(), "analysis.json not found in generated project"
    logger.info("e2e.done | zip=%s | project=%s", zip_path, project_dir)

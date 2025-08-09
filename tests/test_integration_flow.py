import time
from pathlib import Path
import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app


logger = logging.getLogger("ych.test")


def test_generate_with_provided_content():
    logger.info("e2e.generate_only.start")
    client = TestClient(app)

    # Read input content
    content_path = Path(__file__).parent / "message.txt"
    assert content_path.exists(), "tests/message.txt not found"
    content = content_path.read_text(encoding="utf-8")

    # Start generation directly with provided content
    resp = client.post("/generate", json={"content": content, "tone": "professional"})
    assert resp.status_code == 200, resp.text
    gen_id = resp.json()["job_id"]
    logger.info("e2e.generate.queued | job_id=%s", gen_id)

    # Poll generation until done
    deadline = time.time() + 120
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
        time.sleep(1.5)

    assert gen_result is not None, "generation did not complete in time"

    zip_path = gen_result.get("zip_path")
    project_dir = gen_result.get("project_dir")
    assert zip_path and Path(zip_path).exists(), f"missing zip at {zip_path}"
    assert project_dir and Path(project_dir).exists(), f"missing project dir at {project_dir}"

    # Ensure analysis.json exists in generated project for traceability
    analysis_path = Path(project_dir) / "analysis.json"
    assert analysis_path.exists(), "analysis.json not found in generated project"
    logger.info("e2e.done | zip=%s | project=%s", zip_path, project_dir)

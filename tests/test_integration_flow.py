import os
import time
from pathlib import Path
import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app


logger = logging.getLogger("ych.test")


def test_generate_with_provided_content():
    assert os.getenv("FREESTYLE_API_KEY"), "FREESTYLE_API_KEY not set; required for dev server integration test"
    assert os.getenv("FREESTYLE_REPO_ID"), "FREESTYLE_REPO_ID not set; expected an existing provisioned repo to connect to"

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
    deadline = time.time() + 600
    gen_result = None
    while time.time() < deadline:
        r = client.get(f"/generate/{gen_id}")
        assert r.status_code == 200, r.text
        payload = r.json()
        if payload["status"] == "done":
            gen_result = payload["result"]
            break
        if payload["status"] == "error":
            pytest.fail(f"generation error: {payload.get('error')}")
        time.sleep(3)

    assert gen_result is not None, "generation did not complete in time"

    dev = gen_result.get("dev_server") or {}
    assert dev.get("ephemeral_url"), "missing dev server url"
    assert "build" in dev, "missing build logs"
    logger.info("e2e.done | dev=%s", dev.get("ephemeral_url"))

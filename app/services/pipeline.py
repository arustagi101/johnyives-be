from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
import json
import re
from pathlib import Path

from app.models.agents import EvaluationCriterion, CopyPlan, StyleSystem, ContentHierarchy
from app.services.dspy_agents import agent_content_improver, agent_generate_next_page
from app.services.style_guide import default_style, STYLE_GUIDE
from app.services.devserver import connect_dev_server, provision_dev_server
from app.services.mcp_agents import react_generate_and_build


logger = logging.getLogger("ych.pipeline")


def run_full_generation(
    audit_results: Dict[str, Any],
    out_dir: str,
    tone: str = "professional",
    criteria: Optional[List[EvaluationCriterion]] = None,
    content: str | None = None,
) -> Dict[str, Any]:
    artifacts = audit_results.get("artifacts", {})
    dom_path = artifacts.get("dom_sample_path")

    # a) copy: if content provided, improve directly from hierarchical text; else extract from DOM first
    if content is not None:
        copy_plan: CopyPlan = agent_content_improver(content_text=content, tone=tone)
    else:
        html = Path(dom_path).read_text(encoding="utf-8") if dom_path else ""
        # If no explicit content, pass HTML snapshot to content improver which understands hierarchy-like text
        copy_plan = agent_content_improver(content_text=html, tone=tone)

    # b) style
    style: StyleSystem = default_style()

    # c) generate a Next.js homepage using Dev Server and verify build
    # Provision dev server (requires FREESTYLE_API_KEY)
    import os
    api_key = os.getenv("FREESTYLE_API_KEY")
    if not api_key:
        raise RuntimeError("FREESTYLE_API_KEY not set in environment")

    # If a repo id is provided in env, connect; otherwise, provision from template
    repo_id = os.getenv("FREESTYLE_REPO_ID")
    ds = connect_dev_server(api_key, repo_id) if repo_id else provision_dev_server(api_key)

    # Use DSPy React-style agent to write code via MCP tools and verify
    outcome = react_generate_and_build(ds=ds, copy_plan=copy_plan, style_guide=STYLE_GUIDE)

    return {
        "dev_server": {
            "ephemeral_url": ds["ephemeral_url"],
            "mcp_ephemeral_url": ds["mcp_ephemeral_url"],
            "code_server_url": ds["code_server_url"],
            "repo_id": ds["repo_id"],
            "lint": outcome.get("lint"),
            "build": outcome.get("build"),
        },
        "copy_plan": copy_plan.model_dump(),
        "style_system": style.model_dump(),
    }



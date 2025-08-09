from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from app.services.dspy_agents import agent_copywriter, agent_style_system, ExtractHierarchyCoT
from app.services.generator import generate_nextjs_project
from app.models.agents import EvaluationCriterion, CopyPlan, StyleSystem


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

    # a) hierarchy (use provided content if present)
    if content is not None:
        hierarchy = ExtractHierarchyCoT().program(dom_html=content, url=audit_results.get("url", "")).hierarchy_json  # type: ignore[attr-defined]
        # Convert JSON string to object via agent's forward to keep types consistent
        hierarchy_obj = ExtractHierarchyCoT()(dom_html=content, url=audit_results.get("url"))
    else:
        hierarchy_obj = ExtractHierarchyCoT()(dom_html=Path(dom_path).read_text(encoding="utf-8") if dom_path else "", url=audit_results.get("url"))

    # b) copy
    copy_plan: CopyPlan = agent_copywriter(hierarchy_obj, tone=tone)

    # c) style
    style: StyleSystem = agent_style_system(criteria=criteria)

    # d) generate Next.js app
    result = generate_nextjs_project(
        audit_results=audit_results,
        preferences={},
        out_dir=out_dir,
        copy_plan=copy_plan,
        style=style,
    )
    result["copy_plan"] = copy_plan.model_dump()
    result["style_system"] = style.model_dump()
    return result



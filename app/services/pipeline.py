from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
import json
import re
from pathlib import Path

from app.services.generator import generate_nextjs_project
from app.models.agents import EvaluationCriterion, CopyPlan, StyleSystem, ContentHierarchy
from app.services.dspy_agents import agent_content_improver


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
    style: StyleSystem = _default_style()

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


def _default_style() -> StyleSystem:
    return StyleSystem(
        layout_paradigm="modern",
        design_tokens={
            "color_primary": "#0ea5e9",
            "color_secondary": "#111827",
            "font_sans": "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji'",
        },
        components=["Navbar", "Footer", "Hero", "CTASection", "FeatureGrid"],
    )



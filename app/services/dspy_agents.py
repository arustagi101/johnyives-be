from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

import dspy  # type: ignore

from app.models.agents import (
    ContentHierarchy,
    ContentNode,
    CopyPlan,
    CopyBlock,
    StyleSystem,
    EvaluationCriterion,
)


logger = logging.getLogger("ych.dspy")


class ExtractHierarchySig(dspy.Signature):  # type: ignore
    """Extract a concise hierarchical content map from an HTML document.

    Return JSON matching schema:
    {"url": str | null,
     "nodes": [{"id": str, "tag": str, "text": str, "path": str,
                 "children": [... same shape ...]}]}

    Only include salient sections (hero, features, cta, footer, etc.).
    """

    dom_html: str = dspy.InputField()
    url: str = dspy.InputField()
    hierarchy_json: str = dspy.OutputField()


class CopywriterSig(dspy.Signature):  # type: ignore
    """Improve copy for a website, preserving meaning but modernizing tone and clarity.

    Inputs:
    - hierarchy_json: JSON for ContentHierarchy
    - tone: one of [neutral, friendly, professional, bold]

    Output copy_plan_json must match schema:
    {"summary": str,
     "blocks": [{"path": str, "original_text": str, "improved_text": str,
                  "tone": str}]}
    """

    hierarchy_json: str = dspy.InputField()
    tone: str = dspy.InputField()
    copy_plan_json: str = dspy.OutputField()


class ContentImproverSig(dspy.Signature):  # type: ignore
    """Improve provided hierarchical content text into a structured CopyPlan JSON.

    Inputs:
    - content_text: markdown-like text representing site content hierarchy
    - tone: one of [neutral, friendly, professional, bold]

    Output copy_plan_json must match schema exactly:
    {"summary": str,
     "blocks": [{"path": str, "original_text": str, "improved_text": str,
                  "tone": str}]}
    """

    content_text: str = dspy.InputField()
    tone: str = dspy.InputField()
    copy_plan_json: str = dspy.OutputField()


class StyleSig(dspy.Signature):  # type: ignore
    """Propose a modern style system for the site given evaluation criteria.

    Input: criteria_json: [{"key": str, "description": str, "weight": float}]
    Output style_system_json must match schema:
    {"layout_paradigm": "modern"|"classic"|"minimal"|"bold",
     "design_tokens": {"color_primary": str, ...},
     "components": [str]}
    """

    criteria_json: str = dspy.InputField()
    style_system_json: str = dspy.OutputField()


class ExtractHierarchyCoT(dspy.Module):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.program = dspy.ChainOfThought(ExtractHierarchySig)

    def forward(self, dom_html: str, url: str | None = None) -> ContentHierarchy:  # type: ignore[override]
        logger.info("dspy.extract_hierarchy | url=%s", url)
        out = self.program(dom_html=dom_html or "", url=url or "")
        data = json.loads(out.hierarchy_json)
        return ContentHierarchy(**data)


class CopywriterCoT(dspy.Module):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.program = dspy.ChainOfThought(CopywriterSig)

    def forward(self, hierarchy: ContentHierarchy, tone: str = "professional") -> CopyPlan:  # type: ignore[override]
        hierarchy_json = json.dumps(hierarchy.model_dump())
        out = self.program(hierarchy_json=hierarchy_json, tone=tone)
        data = json.loads(out.copy_plan_json)
        # Fill tone if omitted in blocks
        blocks: List[CopyBlock] = []
        for b in data.get("blocks", []):
            if "tone" not in b or not b["tone"]:
                b["tone"] = tone
            blocks.append(CopyBlock(**b))
        return CopyPlan(summary=data.get("summary", "Modernized copy"), blocks=blocks)


class ContentImproverCoT(dspy.Module):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.program = dspy.ChainOfThought(ContentImproverSig)

    def forward(self, content_text: str, tone: str = "professional") -> CopyPlan:  # type: ignore[override]
        out = self.program(content_text=content_text, tone=tone)
        data = json.loads(out.copy_plan_json)
        blocks: List[CopyBlock] = []
        for b in data.get("blocks", []):
            if "tone" not in b or not b["tone"]:
                b["tone"] = tone
            blocks.append(CopyBlock(**b))
        return CopyPlan(summary=data.get("summary", "Modernized copy"), blocks=blocks)


class StyleCoT(dspy.Module):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.program = dspy.ChainOfThought(StyleSig)

    def forward(self, criteria: Optional[List[EvaluationCriterion]] = None) -> StyleSystem:  # type: ignore[override]
        crit = criteria or [EvaluationCriterion(key="clarity", description="Visual clarity", weight=1.0)]
        criteria_json = json.dumps([c.model_dump() for c in crit])
        out = self.program(criteria_json=criteria_json)
        data = json.loads(out.style_system_json)
        return StyleSystem(**data)


def agent_extract_hierarchy(dom_html_path: str, url: Optional[str] = None) -> ContentHierarchy:
    dom_html = Path(dom_html_path).read_text(encoding="utf-8") if dom_html_path else ""
    return ExtractHierarchyCoT()(dom_html=dom_html, url=url)


def agent_copywriter(hierarchy: ContentHierarchy, tone: str = "professional") -> CopyPlan:
    return CopywriterCoT()(hierarchy=hierarchy, tone=tone)


def agent_style_system(criteria: Optional[List[EvaluationCriterion]] = None) -> StyleSystem:
    return StyleCoT()(criteria=criteria)


def agent_content_improver(content_text: str, tone: str = "professional") -> CopyPlan:
    return ContentImproverCoT()(content_text=content_text, tone=tone)



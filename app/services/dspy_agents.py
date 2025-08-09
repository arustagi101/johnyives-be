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


class NextPageGeneratorSig(dspy.Signature):  # type: ignore
    """Generate a Next.js app/page.tsx file given a style guide and improved copy.

    Inputs:
    - style_guide: textual style guide criteria
    - copy_plan_json: the improved copy plan JSON with blocks
    - design_tokens_json: optional design tokens (color_primary, font_sans, etc.)

    Output:
    - page_tsx: A complete Next.js page component (TSX) following the guide
    """

    style_guide: str = dspy.InputField()
    copy_plan_json: str = dspy.InputField()
    design_tokens_json: str = dspy.InputField()
    page_tsx: str = dspy.OutputField()


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


class NextPageGeneratorCoT(dspy.Module):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.program = dspy.ChainOfThought(NextPageGeneratorSig)

    def forward(self, style_guide: str, copy_plan: CopyPlan, style: StyleSystem) -> str:  # type: ignore[override]
        copy_plan_json = json.dumps(copy_plan.model_dump())
        design_tokens_json = json.dumps(style.design_tokens)
        out = self.program(
            style_guide=style_guide,
            copy_plan_json=copy_plan_json,
            design_tokens_json=design_tokens_json,
        )
        return out.page_tsx


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


def agent_generate_next_page(style_guide: str, copy_plan: CopyPlan, style: StyleSystem) -> str:
    return NextPageGeneratorCoT()(style_guide=style_guide, copy_plan=copy_plan, style=style)



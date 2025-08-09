from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel


class EvaluationCriterion(BaseModel):
    key: str
    description: str
    weight: float = 1.0


class ContentNode(BaseModel):
    id: str
    tag: str
    text: str
    path: str
    children: List["ContentNode"] = []


class ContentHierarchy(BaseModel):
    url: Optional[str] = None
    nodes: List[ContentNode]


class CopyBlock(BaseModel):
    path: str
    original_text: str
    improved_text: str
    tone: Literal["neutral", "friendly", "professional", "bold"] = "professional"


class CopyPlan(BaseModel):
    summary: str
    blocks: List[CopyBlock]


class StyleSystem(BaseModel):
    layout_paradigm: Literal["modern", "classic", "minimal", "bold"] = "modern"
    design_tokens: Dict[str, Any]
    components: List[str] = ["Navbar", "Footer", "Hero", "CTASection", "FeatureGrid"]



from typing import Any, Dict, List, Optional
from pydantic import BaseModel, HttpUrl, field_validator


class AuditOptions(BaseModel):
    mobile: bool = True
    viewport_width: int | None = None
    viewport_height: int | None = None


class AuditRequest(BaseModel):
    url: str
    options: Optional[AuditOptions] = None

    @field_validator("url")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class Issue(BaseModel):
    id: str
    category: str
    severity: str
    summary: str
    evidence: Dict[str, Any] | None = None


class Scores(BaseModel):
    accessibility: int | None = None
    performance: int | None = None
    usability: int | None = None


class Artifacts(BaseModel):
    screenshots: List[str] = []
    axe: Dict[str, Any] | None = None
    psi: Dict[str, Any] | None = None
    dom_sample_path: str | None = None


class AuditStatusResponse(BaseModel):
    status: str
    result: Dict[str, Any] | None = None
    error: Dict[str, Any] | None = None


class GeneratePreferences(BaseModel):
    brand_colors: List[str] | None = None
    deploy: bool = False


class GenerateRequest(BaseModel):
    audit_id: str
    preferences: Optional[GeneratePreferences] = None


class GenerateStatusResponse(BaseModel):
    status: str
    result: Dict[str, Any] | None = None
    error: Dict[str, Any] | None = None

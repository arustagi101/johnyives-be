from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging


logger = logging.getLogger("ych.analysis")


def synthesize_suggestions(audit_result: Dict[str, Any]) -> Dict[str, Any]:
    """Return structured suggestions and a simple site plan.

    If DSPy is available, this function can be replaced by a DSPy pipeline that produces
    the same schema. For now, return a rule-based, deterministic output.
    """
    artifacts = audit_result.get("artifacts", {})
    axe = artifacts.get("axe") or {}
    psi = artifacts.get("psi") or {}

    suggestions: List[Dict[str, Any]] = []
    logger.info(
        "analysis.start | has_axe=%s has_psi=%s",
        bool(axe), bool(psi)
    )

    # Accessibility from axe
    for v in (axe.get("violations") or [])[:10]:
        suggestions.append({
            "area": "accessibility",
            "action": v.get("help") or v.get("description") or "Fix accessibility issue",
            "priority": v.get("impact") or "moderate",
            "reference": v.get("helpUrl"),
        })

    # Performance from PSI
    cat = psi.get("lighthouseResult", {}).get("categories", {})
    if cat:
        perf = int(cat.get("performance", {}).get("score", 0) * 100)
        if perf < 80:
            suggestions.append({
                "area": "performance",
                "action": "Optimize images, enable compression, and reduce render-blocking resources.",
                "priority": "high" if perf < 60 else "moderate",
            })

    # Baseline layout suggestions
    suggestions.append({
        "area": "layout",
        "action": "Adopt a consistent 12-column responsive grid, clear visual hierarchy (H1~H3), and prominent CTA in hero.",
        "priority": "moderate",
    })

    plan = {
        "site_map": [
            {"path": "/", "title": "Home"},
            {"path": "/about", "title": "About"},
            {"path": "/contact", "title": "Contact"},
        ],
        "components": [
            "Navbar", "Footer", "Hero", "FeatureGrid", "CTASection", "ContentSection"
        ],
        "design_tokens": {
            "color_primary": "#0ea5e9",
            "color_secondary": "#111827",
            "font_sans": "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\"",
        },
    }

    result = {"suggestions": suggestions, "plan": plan}
    logger.info(
        "analysis.done | suggestions=%s | components=%s",
        len(suggestions), len(plan.get("components", []))
    )
    return result

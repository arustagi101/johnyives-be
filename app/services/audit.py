import asyncio
import logging
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from app.models.schemas import AuditOptions
from app.services.psi import get_psi_report
from app.utils.security import validate_public_url

try:
    from playwright.async_api import async_playwright
except Exception:  # pragma: no cover
    async_playwright = None  # type: ignore


logger = logging.getLogger("ych.audit")

AXE_MIN_JS_URL = (
    "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
)


def perform_audit(url: str, options_dict: Dict[str, Any], out_dir: str) -> Dict[str, Any]:
    validate_public_url(url)
    options = AuditOptions(**options_dict or {})
    logger.info("audit.perform | url=%s | mobile=%s | out_dir=%s", url, options.mobile, out_dir)

    result: Dict[str, Any] = {
        "scores": {},
        "issues": [],
        "artifacts": {"screenshots": []},
        "url": url,
    }

    # Playwright phase
    try:
        pw_data = asyncio.run(_render_and_capture(url, options, out_dir))
        result["artifacts"]["screenshots"] = pw_data.get("screenshots", [])
        result["artifacts"]["dom_sample_path"] = pw_data.get("dom_sample_path")
        if pw_data.get("axe") is not None:
            result["artifacts"]["axe"] = pw_data["axe"]
    except Exception as exc:  # noqa: BLE001
        result.setdefault("warnings", []).append(f"playwright_failed: {exc}")
        logger.warning("audit.playwright_failed | url=%s | err=%s", url, exc)

    # PSI phase (optional)
    try:
        psi = get_psi_report(url, strategy="mobile" if options.mobile else "desktop")
        if psi is not None:
            result["artifacts"]["psi"] = psi
            cat = psi.get("lighthouseResult", {}).get("categories", {})
            perf = int(cat.get("performance", {}).get("score", 0) * 100) if cat else None
            acc = int(cat.get("accessibility", {}).get("score", 0) * 100) if cat else None
            seo = int(cat.get("seo", {}).get("score", 0) * 100) if cat else None
            result["scores"].update({
                "performance": perf,
                "accessibility": acc,
                "usability": seo,
            })
            logger.info("audit.psi | perf=%s acc=%s seo=%s", perf, acc, seo)
    except Exception as exc:  # noqa: BLE001
        result.setdefault("warnings", []).append(f"psi_failed: {exc}")
        logger.warning("audit.psi_failed | url=%s | err=%s", url, exc)

    # Simple heuristics to fill in issues list if empty
    if not result.get("issues"):
        issues = []
        axe = result.get("artifacts", {}).get("axe")
        if axe and axe.get("violations"):
            for v in axe["violations"][:20]:
                issues.append({
                    "id": v.get("id", "axe-issue"),
                    "category": "accessibility",
                    "severity": v.get("impact", "moderate") or "moderate",
                    "summary": v.get("description") or v.get("help") or "Axe violation",
                    "evidence": {"helpUrl": v.get("helpUrl")},
                })
        if not issues:
            issues.append({
                "id": "baseline-review",
                "category": "usability",
                "severity": "info",
                "summary": "No specific issues detected; manual review recommended.",
            })
        result["issues"] = issues

    logger.info("audit.done | url=%s | screenshots=%s | issues=%s", url, len(result.get("artifacts", {}).get("screenshots", [])), len(result.get("issues", [])))
    return result


async def _render_and_capture(url: str, options: AuditOptions, out_dir: str) -> Dict[str, Any]:
    if async_playwright is None:
        raise RuntimeError(
            "playwright not available. Install and run `python -m playwright install chromium`."
        )

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    screenshots: list[str] = []
    dom_sample_path: Optional[str] = None
    axe_result: Optional[Dict[str, Any]] = None

    logger.info("audit.playwright.start | url=%s", url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={
                "width": options.viewport_width or (390 if options.mobile else 1366),
                "height": options.viewport_height or (844 if options.mobile else 768),
            },
            device_scale_factor=1,
            is_mobile=options.mobile,
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        logger.info("audit.playwright.loaded | url=%s", url)

        # Screenshot above-the-fold
        path1 = str(Path(out_dir) / "screenshot_above_fold.png")
        await page.screenshot(path=path1, full_page=False)
        screenshots.append(path1)

        # Full page screenshot (best-effort)
        path2 = str(Path(out_dir) / "screenshot_full.png")
        try:
            await page.screenshot(path=path2, full_page=True)
            screenshots.append(path2)
        except Exception:
            pass

        # DOM sample
        html = await page.content()
        dom_sample_path = str(Path(out_dir) / "dom.html")
        Path(dom_sample_path).write_text(html[:2_000_000], encoding="utf-8")

        # Try axe-core
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(AXE_MIN_JS_URL)
                r.raise_for_status()
                axe_js = r.text
            await page.add_script_tag(content=axe_js)
            axe_result = await page.evaluate("async () => { return await axe.run(); }")
            logger.info("audit.axe.ok | url=%s | violations=%s", url, len((axe_result or {}).get("violations", []) if axe_result else 0))
        except Exception:
            axe_result = None
            logger.info("audit.axe.unavailable | url=%s", url)

        await context.close()
        await browser.close()

    logger.info("audit.playwright.done | url=%s | shots=%s", url, len(screenshots))
    return {
        "screenshots": screenshots,
        "dom_sample_path": dom_sample_path,
        "axe": axe_result,
    }

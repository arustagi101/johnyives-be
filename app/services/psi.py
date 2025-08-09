from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional
import httpx


logger = logging.getLogger("ych.psi")


def get_psi_report(url: str, strategy: str = "mobile") -> Optional[Dict[str, Any]]:
    api_key = os.getenv("PAGESPEED_API_KEY")
    params = {
        "url": url,
        "category": ["PERFORMANCE", "ACCESSIBILITY", "SEO"],
        "strategy": strategy,
    }
    base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    # Without API key, Google still serves some limited requests with quota; we attempt once.
    if api_key:
        params["key"] = api_key

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(base, params=params)
            if resp.status_code >= 400:
                logger.info("psi.http_error | status=%s", resp.status_code)
                return None
            data = resp.json()
            logger.info("psi.ok | strategy=%s", strategy)
            return data
    except Exception:
        logger.warning("psi.error | url=%s", url)
        return None

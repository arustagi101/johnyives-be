from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("ych.dspy.config")


PROVIDER_DEFAULTS = {
    "openai": ("openai/gpt-4o-mini", "OPENAI_API_KEY"),
    "anthropic": ("anthropic/claude-3-7-sonnet-20250219", "ANTHROPIC_API_KEY"),
    "gemini": ("gemini/gemini-2.0-pro", "GEMINI_API_KEY"),
    # Add others if needed
}


def configure_from_env() -> None:
    # Import dspy lazily to avoid hard import error during module import
    try:
        import dspy  # type: ignore
    except Exception as exc:  # pragma: no cover
        logger.exception("DSPy import failed: %s", exc)
        return
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model = os.getenv("LLM_MODEL", "gemini/gemini-2.5-pro")

    if provider not in PROVIDER_DEFAULTS:
        logger.warning("Unknown LLM_PROVIDER=%s; defaulting to openai", provider)
        provider = "openai"

    default_model, key_env = PROVIDER_DEFAULTS[provider]
    api_key = os.getenv(key_env)
    model = model or default_model

    if not api_key:
        logger.error("Missing API key for provider=%s (expected %s)", provider, key_env)
        return

    lm = dspy.LM(model, api_key=api_key, max_tokens=100000)  # type: ignore[arg-type]
    adapter = dspy.TwoStepAdapter(lm)
    dspy.configure(lm=lm, adapter=adapter)
    logger.info("DSPy configured | provider=%s | model=%s", provider, model)


# Configure at import
try:
    configure_from_env()
except Exception as exc:  # pragma: no cover
    logger.exception("Failed to configure DSPy: %s", exc)



"""Live model evaluation harness. Does not invent accuracy when keys are absent."""

from __future__ import annotations

from app.config import get_settings
from app.services.ai.provider import PROMPT_VERSION

PROVIDERS = ("openai", "anthropic", "gemini")


def live_eval_status(n_requested: int = 1000) -> dict:
    settings = get_settings()
    keys = {
        "openai": bool(getattr(settings, "openai_api_key", "")),
        "anthropic": bool(getattr(settings, "anthropic_api_key", "")),
        "gemini": bool(getattr(settings, "gemini_api_key", "")),
    }
    providers = []
    for name in PROVIDERS:
        configured = keys[name]
        providers.append(
            {
                "provider": name,
                "configured": configured,
                "n_run": 0,
                "accuracy": None,
                "latency_ms": None,
                "cost_usd": None,
                "schema_compliance": None,
                "failure_rate": None,
                "status": "unproven" if not configured else "configured_not_run",
            }
        )
    any_key = any(keys.values())
    return {
        "n_requested": n_requested,
        "n_run": 0,
        "prompt_version": PROMPT_VERSION,
        "providers": providers,
        "note": (
            "Live LLM eval was not executed. Keys present: "
            f"{sum(keys.values())}/{len(keys)}. "
            "Do not treat heuristic F1 as live-model accuracy."
            if not any_key
            else "Provider keys exist in this environment but the 1000-example live harness was not run in this pass."
        ),
    }

"""Prompt version registry. Deployment must not proceed on an unevaluated prompt."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.ai.provider import PROMPT_VERSION

REGISTRY_PATH = Path(__file__).with_name("prompt_registry.json")

# accuracy/latency/cost remain None until a live eval writes them.
SEED = [
    {
        "prompt_version": "v1.1.0",
        "model": "heuristic_classifiers",
        "accuracy": None,
        "latency_ms": None,
        "token_cost": None,
        "regression_score": None,
        "status": "active_unevaluated_on_live_llm",
    }
]


def load_registry(path: Path | None = None) -> list[dict]:
    target = path or REGISTRY_PATH
    if not target.exists():
        return list(SEED)
    return json.loads(target.read_text(encoding="utf-8"))


def active_prompt_version() -> str:
    return PROMPT_VERSION


def regression_gate(current: dict | None, previous: dict | None) -> dict:
    if current is None or previous is None:
        return {
            "allow_deploy": False,
            "reason": "Live prompt regression scores are unmeasured. Reject 98 certification.",
        }
    cur = current.get("accuracy")
    prev = previous.get("accuracy")
    if cur is None or prev is None:
        return {
            "allow_deploy": False,
            "reason": "Accuracy is null. Do not deploy on missing live eval.",
        }
    if cur + 0.01 < prev:
        return {"allow_deploy": False, "reason": f"Accuracy dropped from {prev} to {cur}."}
    return {"allow_deploy": True, "reason": "No measured live regression."}


def registry_report() -> dict:
    rows = load_registry()
    return {
        "active": active_prompt_version(),
        "entries": rows,
        "gate": regression_gate(None, None),
    }

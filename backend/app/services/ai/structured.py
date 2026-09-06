from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.services.ai.firewall import sanitize_model_output
from app.services.ai.provider import complete_with_fallback, parse_json_object

log = get_logger("ai.structured")

ANALYZER_SCHEMA = {
    "type": "object",
    "required": ["summary", "findings", "score"],
    "properties": {
        "summary": {"type": "string", "minLength": 8, "maxLength": 1200},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "findings": {
            "type": "array",
            "maxItems": 20,
            "items": {
                "type": "object",
                "required": ["explanation", "suggestion"],
                "properties": {
                    "explanation": {"type": "string"},
                    "suggestion": {"type": "string"},
                    "severity": {"type": "string"},
                },
            },
        },
    },
    "additionalProperties": True,
}


def complete_validated_json(prompt: str, schema: dict[str, Any] | None = None, *, strong: bool = True) -> dict[str, Any] | None:
    schema = schema or ANALYZER_SCHEMA
    last_tokens = 0
    for attempt in range(3):
        response = complete_with_fallback(prompt, strong=strong or attempt > 0)
        if response is None:
            continue
        last_tokens = response.tokens
        cleaned = sanitize_model_output(response.content)
        if cleaned is None:
            log.warning("ai_output_blocked_leakage", attempt=attempt)
            continue
        try:
            data = parse_json_object(cleaned)
            _validate(data, schema)
            data["_tokens"] = last_tokens
            data["_model"] = response.model
            return data
        except Exception as exc:  # noqa: BLE001
            log.warning("ai_output_invalid", attempt=attempt, error=str(exc))
    return None


def _validate(data: dict[str, Any], schema: dict[str, Any]) -> None:
    try:
        import jsonschema

        jsonschema.validate(data, schema)
        return
    except ImportError:
        pass
    for key in schema.get("required", []):
        if key not in data:
            raise ValueError(f"Missing required key {key}")
    if "score" in data and not isinstance(data["score"], int):
        raise ValueError("score must be an integer")

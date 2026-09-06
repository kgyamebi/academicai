from __future__ import annotations

from app.core.logging import get_logger
from app.services.ai.provider import (
    PROMPT_VERSION,
    complete_with_fallback,
    parse_json_object,
    wrap_untrusted,
)
from app.services.analysis.engine import AnalysisResult

log = get_logger("ai.enhance")


def enhance_analysis(result: AnalysisResult, document_excerpt: str) -> tuple[AnalysisResult, int, str]:
    """Optionally enrich summary and weakest-area guidance. Heuristic scores remain source of truth unless schema-valid."""
    if not document_excerpt.strip():
        return result, 0, PROMPT_VERSION
    prompt = (
        "Return JSON with keys: summary (string), priority_actions (array of up to 5 strings), "
        "weakest_area_how_to_improve (string). Do not invent sources or grades.\n"
        + wrap_untrusted("QUESTION", result.question.raw_text)
        + wrap_untrusted("DOCUMENT_EXCERPT", document_excerpt[:8000])
        + wrap_untrusted(
            "EXISTING_DIAGNOSTIC",
            f"Overall {result.overall_score}. Weakest: {result.weakest_area}. Priorities: {result.priority_actions}",
        )
    )
    response = complete_with_fallback(prompt, strong=True)
    if response is None:
        return result, 0, PROMPT_VERSION
    try:
        data = parse_json_object(response.content)
    except Exception as exc:  # noqa: BLE001
        log.warning("ai_output_rejected", error=str(exc))
        return result, response.tokens, response.prompt_version
    if isinstance(data.get("summary"), str) and data["summary"].strip():
        result.summary = data["summary"].strip()[:1200]
    actions = data.get("priority_actions")
    if isinstance(actions, list):
        cleaned = [str(a).strip() for a in actions if str(a).strip()][:5]
        if cleaned:
            result.priority_actions = cleaned
    improve = data.get("weakest_area_how_to_improve")
    if isinstance(improve, str) and improve.strip():
        result.weakest_area["how_to_improve"] = improve.strip()[:800]
    return result, response.tokens, response.prompt_version


def coach_reply(question: str, assignment_context: str) -> tuple[str, int]:
    prompt = (
        "Answer the student as an academic writing coach. Use only the provided assignment context. "
        "Do not invent sources, quotations, statistics, page numbers, or hidden lecturer rules. "
        "Return JSON {\"answer\": string}.\n"
        + wrap_untrusted("STUDENT_QUESTION", question)
        + wrap_untrusted("ASSIGNMENT_CONTEXT", assignment_context[:12000])
    )
    response = complete_with_fallback(prompt, strong=True)
    if response is None:
        return _heuristic_coach(question, assignment_context), 0
    try:
        data = parse_json_object(response.content)
        answer = str(data.get("answer") or "").strip()
        if answer:
            return answer, response.tokens
    except Exception:
        pass
    return _heuristic_coach(question, assignment_context), response.tokens


def _heuristic_coach(question: str, context: str) -> str:
    q = question.lower()
    if "thesis" in q:
        return (
            "A weak thesis usually restates the topic instead of answering the question. "
            "Write one sentence that takes a position a reader could dispute, then check that each body paragraph supports that position. "
            "I will not rewrite the whole assignment for you — draft the claim in your own words, then re-check."
        )
    if "paragraph" in q:
        return (
            "A paragraph is usually stronger when it has a topic sentence, evidence, an explanation of why the evidence matters, "
            "and a link back to the thesis. If paragraph 4 only reports information, add the 'so what' sentence."
        )
    if "question" in q or "mean" in q:
        return (
            "Look at the command words first (compare, evaluate, discuss). Those tell you the intellectual task. "
            "Then identify the topic and any limits of place or time. Based on the wording, those appear to be the main requirements — "
            "not a claim about what a particular lecturer wants."
        )
    if "evidence" in q:
        return (
            "Claims that use statistics, historical facts, or research findings usually need a citation. "
            "Missing a citation does not make a sentence false; it means a marker cannot verify it. Add a real source you have read."
        )
    if "relevance" in q:
        return (
            "A relevance score falls when the draft drifts from the question or skips a required move such as evaluation. "
            "Map each paragraph to a requirement of the question and cut unsupported tangents."
        )
    return (
        "Use the report's priority actions first. Explain the problem, then revise that section yourself. "
        "I can teach the concept and suggest a direction, but I will not generate a full assignment for submission."
    )

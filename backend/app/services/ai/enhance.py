from __future__ import annotations

from app.core.logging import get_logger
from app.services.ai.firewall import (
    looks_like_injection,
    untrusted_corpus_is_injection,
    wrap_layers,
)
from app.services.ai.hallucination import allow_model_text
from app.services.ai.provider import PROMPT_VERSION, SYSTEM_PROMPT, wrap_untrusted
from app.services.ai.structured import complete_validated_json
from app.services.analysis.engine import AnalysisResult

log = get_logger("ai.enhance")


def enhance_analysis(result: AnalysisResult, document_excerpt: str) -> tuple[AnalysisResult, int, str]:
    """Optionally enrich summary and weakest-area guidance. Heuristic scores remain source of truth unless schema-valid."""
    if not document_excerpt.strip():
        return result, 0, PROMPT_VERSION
    if untrusted_corpus_is_injection(document_excerpt, result.question.raw_text):
        log.warning("ai_enhance_skipped_untrusted_injection")
        return result, 0, PROMPT_VERSION
    diagnostic = f"Overall {result.overall_score}. Weakest: {result.weakest_area}. Priorities: {result.priority_actions}"
    user_request = (
        "Return JSON with keys: summary (string), priority_actions (array of up to 5 strings), "
        "score (integer 0-100 matching the existing overall only if you agree, else the existing score), "
        "findings (array). Do not invent sources, statistics, quotations, page numbers, or grades."
    )
    prompt = wrap_layers(
        system=SYSTEM_PROMPT,
        user=user_request,
        document=document_excerpt[:8000],
        reference=wrap_untrusted("QUESTION", result.question.raw_text)
        + wrap_untrusted("EXISTING_DIAGNOSTIC", diagnostic),
    )
    data = complete_validated_json(prompt, strong=True)
    if data is None:
        return result, 0, PROMPT_VERSION
    tokens = int(data.get("_tokens") or 0)
    version = str(data.get("_model") or PROMPT_VERSION)
    blob = f"{data.get('summary', '')} {data.get('priority_actions', '')} {data.get('weakest_area_how_to_improve', '')}"
    if not allow_model_text(blob, f"{document_excerpt}\n{diagnostic}\n{result.summary}"):
        log.warning("ai_enhance_blocked_hallucination")
        return result, tokens, PROMPT_VERSION
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
    return result, tokens, version


def coach_reply(question: str, assignment_context: str) -> tuple[str, int]:
    if looks_like_injection(question):
        return _heuristic_coach(question, assignment_context), 0
    prompt = wrap_layers(
        system=SYSTEM_PROMPT,
        user=(
            "Answer the student as an academic writing coach. Use only the provided assignment context. "
            "Do not invent sources, quotations, statistics, page numbers, or hidden lecturer rules. "
            "Return JSON {\"answer\": string}."
        ),
        document=question,
        reference=assignment_context[:12000],
    )
    data = complete_validated_json(
        prompt,
        schema={
            "type": "object",
            "required": ["answer"],
            "properties": {"answer": {"type": "string", "minLength": 8, "maxLength": 2500}},
            "additionalProperties": True,
        },
        strong=True,
    )
    if data is None:
        return _heuristic_coach(question, assignment_context), 0
    answer = str(data.get("answer") or data.get("summary") or "").strip()
    tokens = int(data.get("_tokens") or 0)
    if answer and allow_model_text(answer, assignment_context):
        if _coach_is_misconduct(answer):
            return _heuristic_coach(question, assignment_context), tokens
        return answer, tokens
    return _heuristic_coach(question, assignment_context), tokens


def _coach_is_misconduct(answer: str) -> bool:
    blob = answer.lower()
    if len(answer.split()) > 350:
        return True
    return any(
        phrase in blob
        for phrase in (
            "here is a complete essay",
            "you can submit this",
            "references i invented",
            "made-up source",
        )
    )


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

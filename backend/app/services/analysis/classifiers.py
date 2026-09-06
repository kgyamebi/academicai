"""Deterministic academic classifiers used by the analysis engine and eval harness.

Labels follow writing-centre rules, not model self-agreement:
- A thesis is a contestable answer to the question, not a topic label.
- An argument contains a claim plus a reason or consequence.
- Evidence that cites quantities, studies, or historical facts usually needs a source.
- Rubric criteria are covered when the mapped diagnostic score is at least 55.
"""

from __future__ import annotations

import re

THESIS_MARKERS = re.compile(
    r"\b(this (paper|essay|assignment|study|article|dissertation) argues|"
    r"i (argue|contend|claim)|this essay argues|it (will be )?argued|"
    r"the (central|main) (claim|argument)|this dissertation argues|"
    r"the central claim is)\b",
    re.I,
)
TOPIC_LABEL = re.compile(
    r"\b(this (essay|paper|assignment|article) (is about|will (discuss|talk|look|explore)|discusses)|"
    r"interesting topic|i will (talk|discuss|write)|the topic of this)\b",
    re.I,
)
CONTESTABLE = re.compile(
    r"\b(should|must|argues?|contend|because|unless|rather than|not (only|merely)|"
    r"more (important|effective)|limited|fails|succeeds|depends|outweigh|"
    r"only insofar|determines outcomes)\b",
    re.I,
)
CLAIM_MARKERS = re.compile(
    r"\b(therefore|thus|this shows|this suggests|it is clear|demonstrates|argues that|"
    r"this means|consequently|as a result|because|so that)\b",
    re.I,
)
DESCRIPTIVE_ONLY = re.compile(
    r"\b(there (is|are)|this section|the next (chapter|section)|lists definitions|"
    r"background material|many books|literature on)\b",
    re.I,
)
SPECIFIC_CLAIM = re.compile(
    r"\b(\d+\s?%|\d{1,3}\spercent|gdp|inflation|unemployment|study found|"
    r"research (indicates|shows|suggests)|statistics show|a study)\b",
    re.I,
)
CITATION = re.compile(
    r"\(([A-Z][A-Za-z'’\-]+(?:,\s*(?:&|and)\s*[A-Z][A-Za-z'’\-]+)?),?\s*(?:19|20)\d{2}"
    r"|[A-Z][A-Za-z'’\-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z'’\-]+)?(?:\s+et\s+al\.)?\s+\((?:19|20)\d{2}"
)
STOP = {
    "the", "and", "for", "that", "with", "this", "from", "your", "are", "was",
    "were", "have", "has", "had", "not", "but", "you", "their", "they", "them",
    "into", "onto", "about", "than", "then", "also", "such", "using", "use",
}


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]{3,}", (text or "").lower()) if t not in STOP}


def classify_thesis(draft: str, question: str) -> str:
    text = (draft or "").strip()
    if not text:
        return "missing"
    if TOPIC_LABEL.search(text) and not CONTESTABLE.search(text):
        return "weak"
    overlap = tokens(text) & tokens(question)
    if THESIS_MARKERS.search(text) or (CONTESTABLE.search(text) and overlap):
        if len(text.split()) < 10:
            return "weak"
        return "strong"
    if CONTESTABLE.search(text) and not overlap:
        return "weak"
    return "missing"


def has_reasoned_argument(text: str) -> bool:
    blob = text or ""
    if CLAIM_MARKERS.search(blob) and not (DESCRIPTIVE_ONLY.search(blob) and not CLAIM_MARKERS.search(blob)):
        return True
    return bool(CLAIM_MARKERS.search(blob))


def needs_citation(text: str) -> bool:
    blob = text or ""
    if not SPECIFIC_CLAIM.search(blob):
        return False
    if CITATION.search(blob):
        return False
    return True


def rubric_covered(criteria: list[dict], scores: dict[str, int]) -> set[str]:
    aliases = {
        "argument": "argument",
        "evidence": "evidence",
        "structure": "structure",
        "critical analysis": "argument",
        "critical": "argument",
        "referencing": "citations",
        "citation": "citations",
        "references": "references",
        "writing": "academic_writing",
        "language": "grammar",
        "grammar": "grammar",
        "relevance": "relevance",
        "thesis": "thesis",
        "content": "relevance",
        "evaluation": "relevance",
        "judgement": "relevance",
        "analyze": "argument",
        "analyse": "argument",
    }
    covered: set[str] = set()
    for item in criteria:
        name = str(item.get("name") or "")
        key = "academic_writing"
        lowered = name.lower()
        for alias, mapped in aliases.items():
            if alias in lowered:
                key = mapped
                break
        if scores.get(key, 0) >= 55:
            covered.add(name)
    return covered

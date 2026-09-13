"""Reject model text that invents sources, statistics, or locators.

Allowed text is the student document plus the already-computed diagnostic.
If a citation, DOI, page locator, or percentage does not appear there, the
output is dropped and the caller must use the heuristic result.
"""

from __future__ import annotations

import re

from app.core.metrics import incr

CITATION_LIKE = re.compile(
    r"\b[A-Z][A-Za-z'’\-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z'’\-]+)?(?:\s+et\s+al\.)?\s*\((?:19|20)\d{2}[a-z]?\)"
    r"|\((?:[A-Z][A-Za-z'’\-]+),?\s*(?:19|20)\d{2}[a-z]?\)"
)
DOI_LIKE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
PAGE_LIKE = re.compile(r"\b(?:p{1,2}\.?|page)\s*\d{2,4}\b", re.I)
PERCENT_LIKE = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%|\b\d{1,3}\spercent\b", re.I)
QUOTE_LIKE = re.compile(r"[“\"][^”\"]{20,}[”\"]")
JOURNAL_LIKE = re.compile(
    r"\b(Journal of|Review of|Quarterly Journal|Proceedings of the)\b",
    re.I,
)
LECTURER_EXPECT = re.compile(
    r"\b(your (lecturer|tutor|professor|marker) (expects|wants|requires)|"
    r"the (module leader|examiner) (always|secretly))\b",
    re.I,
)
FABRICATED_STUDY = re.compile(
    r"\b(unpublished (trial|study) at|imaginary cohort of|fictional sample of \d+)\b",
    re.I,
)


def allow_model_text(output: str, allowed: str) -> bool:
    if not (output or "").strip():
        return False
    haystack = (allowed or "").lower()
    for pattern in (
        CITATION_LIKE,
        DOI_LIKE,
        PAGE_LIKE,
        PERCENT_LIKE,
        QUOTE_LIKE,
        JOURNAL_LIKE,
        LECTURER_EXPECT,
        FABRICATED_STUDY,
    ):
        for match in pattern.finditer(output):
            snippet = match.group(0).strip().lower()
            if snippet and snippet not in haystack:
                incr("ai.hallucination_blocked")
                return False
    return True

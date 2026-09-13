"""Reference lookup. Never invent a match. Missing APIs yield could_not_verify."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import httpx

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger("verify_sources")

STATUSES = ("verified", "likely_match", "needs_review", "could_not_verify")
_DOI_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9./();:_-]{0,255}$")


@dataclass
class Verification:
    status: str
    confidence: int
    explanation: str
    provider: str
    provider_id: str | None = None
    matched_title: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def verify_reference(*, title: str = "", doi: str = "", year: str = "") -> Verification:
    doi = _safe_doi(doi)
    title = (title or "").strip()
    if not doi and not title:
        return Verification("could_not_verify", 0, "No DOI or title was available to look up.", "none")
    settings = get_settings()
    if doi:
        result = _crossref_doi(doi, settings.crossref_mailto)
        if result:
            return result
    if title:
        result = _openalex_title(title, settings.openalex_email)
        if result:
            return result
        result = _semantic_scholar_title(title, settings.semantic_scholar_api_key)
        if result:
            return result
    return Verification(
        "could_not_verify",
        0,
        "No bibliographic service returned a match. The reference was not marked verified.",
        "none",
    )


def _safe_doi(doi: str) -> str:
    cleaned = (doi or "").strip()
    if not cleaned or "://" in cleaned or "\\" in cleaned or cleaned.startswith("/") or "@" in cleaned:
        return ""
    if not _DOI_SAFE.fullmatch(cleaned):
        return ""
    return cleaned


def _crossref_doi(doi: str, mailto: str) -> Verification | None:
    url = f"https://api.crossref.org/works/{doi}"
    try:
        with httpx.Client(timeout=4.0) as client:
            response = client.get(url, headers={"User-Agent": f"AcademicCheckAI/1.0 (mailto:{mailto})"})
    except Exception as exc:
        log.debug("crossref_request_failed", doi=doi, error=str(exc))
        return None
    if response.status_code == 404:
        return Verification("could_not_verify", 10, "Crossref has no work for this DOI.", "crossref", doi)
    if response.status_code != 200:
        return None
    try:
        message = response.json().get("message") or {}
    except Exception as exc:
        log.debug("crossref_parse_failed", doi=doi, error=str(exc))
        return None
    found_doi = str(message.get("DOI") or "").lower()
    if found_doi and found_doi == doi.lower():
        title = " ".join(message.get("title") or []) or None
        return Verification("verified", 90, "Crossref returned the same DOI.", "crossref", doi, title)
    return Verification("needs_review", 40, "Crossref responded but the DOI did not match exactly.", "crossref", doi)


def _openalex_title(title: str, email: str) -> Verification | None:
    try:
        with httpx.Client(timeout=4.0) as client:
            response = client.get(
                "https://api.openalex.org/works",
                params={"search": title, "per_page": 1, "mailto": email},
            )
    except Exception as exc:
        log.debug("openalex_request_failed", error=str(exc))
        return None
    if response.status_code != 200:
        return None
    try:
        results = (response.json().get("results") or [])
    except Exception as exc:
        log.debug("openalex_parse_failed", error=str(exc))
        return None
    if not results:
        return Verification("could_not_verify", 10, "OpenAlex returned no works for this title.", "openalex")
    found = str(results[0].get("display_name") or "")
    if found.lower().strip() == title.lower().strip():
        return Verification("likely_match", 70, "OpenAlex top hit has the same display title.", "openalex", None, found)
    return Verification(
        "needs_review",
        35,
        "OpenAlex returned a candidate that is not an exact title match. It was not auto-verified.",
        "openalex",
        None,
        found,
    )


def _semantic_scholar_title(title: str, api_key: str) -> Verification | None:
    headers = {"User-Agent": "AcademicCheckAI/1.0"}
    if api_key:
        headers["x-api-key"] = api_key
    try:
        with httpx.Client(timeout=4.0) as client:
            response = client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": title, "limit": 1, "fields": "title,externalIds"},
                headers=headers,
            )
    except Exception as exc:
        log.debug("semantic_scholar_request_failed", error=str(exc))
        return None
    if response.status_code != 200:
        return None
    try:
        data = response.json().get("data") or []
    except Exception as exc:
        log.debug("semantic_scholar_parse_failed", error=str(exc))
        return None
    if not data:
        return Verification("could_not_verify", 10, "Semantic Scholar returned no papers for this title.", "semantic_scholar")
    found = str(data[0].get("title") or "")
    if found.lower().strip() == title.lower().strip():
        return Verification(
            "likely_match",
            65,
            "Semantic Scholar top hit has the same title. It was not auto-verified without a DOI match.",
            "semantic_scholar",
            None,
            found,
        )
    return Verification(
        "needs_review",
        30,
        "Semantic Scholar returned a candidate that is not an exact title match. It was not auto-verified.",
        "semantic_scholar",
        None,
        found,
    )

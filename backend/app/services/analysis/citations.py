from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

APA_PAREN = re.compile(
    r"\((?:[A-Z][A-Za-z'’\-]+(?:\s+(?:&|and)\s+[A-Z][A-Za-z'’\-]+)?(?:\s+et\s+al\.)?"
    r"(?:,\s*(?:&|and)\s*[A-Z][A-Za-z'’\-]+)?),?\s*(?:19|20)\d{2}[a-z]?"
    r"(?:,\s*p+\.?\s*\d+[-–]?\d*)?\)"
)
APA_NARRATIVE = re.compile(
    r"\b[A-Z][A-Za-z'’\-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z'’\-]+)?(?:\s+et\s+al\.)?\s+\((?:19|20)\d{2}[a-z]?\)"
)
MLA_PAREN = re.compile(r"\([A-Z][A-Za-z'’\-]+(?:\s+and\s+[A-Z][A-Za-z'’\-]+)?\s+\d{1,4}\)")
IEEE_PAREN = re.compile(r"\[(\d{1,3}(?:\s*[-–,]\s*\d{1,3})*)\]")
DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
URL = re.compile(r"https?://\S+")
YEAR = re.compile(r"\b((?:19|20)\d{2})\b")


@dataclass
class ParsedCitation:
    raw_text: str
    style_guess: str
    author: str | None = None
    year: str | None = None
    locator: str | None = None
    paragraph_index: int | None = None
    char_start: int = 0
    char_end: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ParsedReference:
    raw_text: str
    author: str | None = None
    year: str | None = None
    title: str | None = None
    journal: str | None = None
    publisher: str | None = None
    doi: str | None = None
    url: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    sort_order: int = 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_fields"] = ", ".join(self.missing_fields)
        return data


@dataclass
class CitationReport:
    citations: list[ParsedCitation]
    references: list[ParsedReference]
    mismatches: list[str]
    duplicates: list[str]
    style_consistency: str
    summary: str

    def to_dict(self) -> dict:
        return {
            "citations": [c.to_dict() for c in self.citations],
            "references": [r.to_dict() for r in self.references],
            "mismatches": self.mismatches,
            "duplicates": self.duplicates,
            "style_consistency": self.style_consistency,
            "summary": self.summary,
            "in_text_count": len(self.citations),
            "reference_count": len(self.references),
        }


def analyze_citations(text: str, paragraphs: list, style: str = "apa7") -> CitationReport:
    citations = _extract_citations(text, paragraphs, style)
    references = _extract_references(text, paragraphs)
    mismatches = _mismatches(citations, references)
    duplicates = _duplicates(references)
    consistency = _style_consistency(citations, style)
    summary = (
        f"In-text citations: {len(citations)}. References: {len(references)}. "
        f"{len(mismatches)} citation(s) may not have matching references."
    )
    return CitationReport(citations, references, mismatches, duplicates, consistency, summary)


def _extract_citations(text: str, paragraphs: list, style: str) -> list[ParsedCitation]:
    found: list[ParsedCitation] = []
    patterns: list[tuple[re.Pattern, str]] = []
    if style in {"apa7", "harvard", "chicago"}:
        patterns = [(APA_PAREN, style), (APA_NARRATIVE, style)]
    elif style == "mla9":
        patterns = [(MLA_PAREN, "mla9"), (APA_PAREN, "possible-apa")]
    elif style == "ieee":
        patterns = [(IEEE_PAREN, "ieee")]
    else:
        patterns = [(APA_PAREN, style), (MLA_PAREN, "mla9"), (IEEE_PAREN, "ieee")]

    seen: set[tuple[int, int]] = set()
    for pattern, guess in patterns:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if span in seen:
                continue
            seen.add(span)
            raw = match.group(0)
            para_idx = _paragraph_index(paragraphs, match.start())
            year = None
            ym = YEAR.search(raw)
            if ym:
                year = ym.group(1)
            author = _author_from_citation(raw)
            found.append(
                ParsedCitation(
                    raw_text=raw,
                    style_guess=guess,
                    author=author,
                    year=year,
                    paragraph_index=para_idx,
                    char_start=match.start(),
                    char_end=match.end(),
                )
            )
    return found


def _extract_references(text: str, paragraphs: list) -> list[ParsedReference]:
    start = None
    for p in paragraphs:
        heading = p.text.lower()
        if p.is_heading and any(k in heading for k in ("reference", "bibliograph", "works cited")):
            start = p.index
            break
    if start is None:
        # Last 15% of paragraphs that look like bibliographic lines.
        candidates = [p for p in paragraphs if _looks_like_reference(p.text)]
        source = candidates[-40:]
    else:
        source = [p for p in paragraphs if p.index > start and not p.is_heading]

    refs: list[ParsedReference] = []
    for i, p in enumerate(source):
        if not _looks_like_reference(p.text) and start is None:
            continue
        if len(p.text.split()) < 6:
            continue
        doi = None
        dm = DOI.search(p.text)
        if dm:
            doi = dm.group(0)
        url = None
        um = URL.search(p.text)
        if um:
            url = um.group(0).rstrip(").,")
        year = None
        ym = YEAR.search(p.text)
        if ym:
            year = ym.group(1)
        author = p.text.split(".")[0][:200] if "." in p.text else p.text.split(",")[0][:200]
        title = _title_guess(p.text)
        missing = []
        if not author or len(author) < 3:
            missing.append("author")
        if not year:
            missing.append("date")
        if not title:
            missing.append("title")
        refs.append(
            ParsedReference(
                raw_text=p.text,
                author=author,
                year=year,
                title=title,
                doi=doi,
                url=url,
                missing_fields=missing,
                sort_order=i,
            )
        )
    return refs


def _looks_like_reference(text: str) -> bool:
    blob = text.strip()
    if DOI.search(blob) or URL.search(blob):
        return True
    if re.match(r"^[A-Z][A-Za-z'’\-]+,\s+[A-Z]", blob) and YEAR.search(blob):
        return True
    if YEAR.search(blob) and len(blob) > 40 and "," in blob:
        return True
    if re.match(r"^\[\d+\]", blob):
        return True
    return False


def _title_guess(text: str) -> str | None:
    quoted = re.search(r"[“\"](.+?)[”\"]", text)
    if quoted:
        return quoted.group(1)
    italicish = re.search(r"\.\s+([A-Z][^.!?]{12,120})\.", text)
    if italicish:
        return italicish.group(1)
    return None


def _author_from_citation(raw: str) -> str | None:
    cleaned = raw.strip("()[]")
    cleaned = re.sub(r"(?:19|20)\d{2}[a-z]?", "", cleaned)
    cleaned = re.sub(r"p+\.?\s*\d+[-–]?\d*", "", cleaned, flags=re.I)
    cleaned = cleaned.replace(",", " ").replace("&", " ").strip()
    return cleaned[:120] or None


def _paragraph_index(paragraphs: list, pos: int) -> int | None:
    for p in paragraphs:
        if p.char_start <= pos <= p.char_end:
            return p.index
    return None


def _norm_author(value: str | None) -> str:
    if not value:
        return ""
    token = re.sub(r"[^A-Za-z\-]", " ", value).split()
    return token[0].lower() if token else ""


def _mismatches(citations: list[ParsedCitation], references: list[ParsedReference]) -> list[str]:
    ref_authors = {_norm_author(r.author) for r in references if _norm_author(r.author)}
    ref_years = {r.year for r in references if r.year}
    issues = []
    if not references and citations:
        issues.append("In-text citations were found, but a reference list was not clearly detected.")
        return issues
    for c in citations:
        author = _norm_author(c.author)
        if author and ref_authors and author not in ref_authors:
            if c.year and c.year not in ref_years:
                issues.append(f"{c.raw_text} may not have a matching reference.")
            elif author not in ref_authors:
                issues.append(f"{c.raw_text} may not have a matching reference.")
    # Unique while preserving order
    return list(dict.fromkeys(issues))


def _duplicates(references: list[ParsedReference]) -> list[str]:
    seen: dict[str, int] = {}
    dups = []
    for r in references:
        key = f"{_norm_author(r.author)}|{r.year}|{(r.title or r.raw_text[:40]).lower()}"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 2:
            dups.append(r.raw_text[:160])
    return dups


def _style_consistency(citations: list[ParsedCitation], expected: str) -> str:
    if not citations:
        return "No in-text citations were detected, so style consistency could not be assessed."
    guesses = {c.style_guess for c in citations}
    if len(guesses) == 1:
        return f"Detected in-text citations appear broadly consistent with {expected}."
    return "In-text citations appear to mix styles. Check that the whole document follows one required style."

"""Unlabeled citation parser corpus.

These strings exercise the extractor. They are not gold labels.
Do not compute F1 against strings generated from the same regexes.
"""

from __future__ import annotations

from app.services.analysis.citations import analyze_citations
from app.services.documents.extractor import ExtractedParagraph

AUTHORS = (
    "Sen",
    "Rodrik",
    "Stiglitz",
    "Acemoglu",
    "Mkandawire",
    "Chang",
    "Ostrom",
    "North",
    "Fanon",
    "Mbembe",
    "Amsden",
    "Wade",
    "Evans",
    "Khan",
    "Nkrumah",
    "Ake",
    "Smith",
    "Jones",
    "Patel",
    "Nguyen",
)
YEARS = (1989, 1991, 1995, 1999, 2001, 2002, 2007, 2011, 2012, 2015, 2018, 2020)
STYLES = ("apa7", "mla9", "harvard", "chicago", "ieee")


def citation_parser_cases() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    idx = 1
    for author in AUTHORS:
        for year in YEARS:
            cases.append((f"{author} ({year}) discusses institutions.", "apa7"))
            cases.append((f"The claim is contested ({author}, {year}).", "apa7"))
            cases.append((f"Capability matters ({author} {year}).", "harvard"))
            cases.append((f"({author} {year}, 44) uses a locator.", "chicago"))
            cases.append((f"({author} {idx}) is page-number MLA-like.", "mla9"))
            cases.append((f"Prior work [{idx}] frames the case.", "ieee"))
            cases.append((f"{author} writes without a year in this sentence.", "apa7"))
            cases.append((f"Incomplete: ({author}).", "apa7"))
            cases.append((f"{author} ({year}) and also [{idx}] mixed in one sentence.", "apa7"))
            cases.append(
                (
                    f"Trade rose ({author}, {year}).\n\nReferences\n{author}, A. ({year}). "
                    f"Placeholder title for parser robustness. W. W. Norton.",
                    "apa7",
                )
            )
            idx = 1 if idx >= 99 else idx + 1
    # Malformed / mixed leftovers to keep n well above 2000
    for author in AUTHORS:
        cases.append((f"See also recent commentary by {author} without a year.", "apa7"))
        cases.append((f"{author} (99) is not a four-digit year.", "apa7"))
    return cases


def parser_robustness() -> dict:
    cases = citation_parser_cases()
    failures = 0
    extracted = 0
    for text, style in cases:
        try:
            report = analyze_citations(text, _paragraphs(text), style)
        except Exception:
            failures += 1
            continue
        extracted += len(report.citations) + len(report.references)
    n = len(cases)
    return {
        "n": n,
        "failures": failures,
        "extracted_spans": extracted,
        "failure_rate": (failures / n) if n else 1.0,
        "labeled_for_f1": False,
        "note": "Robustness corpus is unlabeled. Do not report F1 on these strings.",
    }


def _paragraphs(text: str) -> list[ExtractedParagraph]:
    blocks = [b.strip() for b in text.split("\n") if b.strip()] or [text]
    paras = []
    cursor = 0
    for i, block in enumerate(blocks):
        heading = block.lower() in {"references", "bibliography", "works cited"}
        paras.append(
            ExtractedParagraph(
                index=i,
                text=block,
                is_heading=heading,
                heading_level=1 if heading else 0,
                char_start=cursor,
                char_end=cursor + len(block),
                word_count=len(block.split()),
            )
        )
        cursor += len(block) + 1
    return paras

"""Adversarial hallucination cases. These are red-team strings, not lecturer gold."""

from __future__ import annotations

from app.services.ai.hallucination import allow_model_text

ALLOWED = "Industrial policy matters in developing economies. Diagnostic overall 70. Weakest: evidence."

AUTHORS = (
    "Fictional",
    "Nonexistent",
    "Placeholder",
    "Invented",
    "Bogus",
    "UnpublishedAuthor",
    "Ghostwriter",
    "Fabricated",
    "Imaginary",
    "Synthetic",
    "PseudoScholar",
    "Mockett",
    "Notareal",
    "DummyCite",
    "FalseAuthor",
    "ShadowRef",
    "Phantom",
    "Apochrypha",
    "Unsourced",
    "Madeup",
)
JOURNALS = (
    "Journal of Imaginary Economics",
    "Review of Nonexistent Policy",
    "Quarterly Journal of Fake Trade",
    "Proceedings of the Invented Academy",
    "Journal of Placeholder Development",
    "Journal of Counterfeit Health Systems",
    "Review of Fabricated Law",
    "Quarterly Journal of Ghost Engineering",
    "Proceedings of the Placeholder Society",
    "Journal of Imaginary Medicine",
    "Review of Synthetic History",
    "Quarterly Journal of Dummy Physics",
    "Journal of Invented Education",
    "Review of Bogus Climate Policy",
    "Proceedings of the Fictional Senate",
    "Journal of Placeholder Linguistics",
    "Review of Nonexistent Ethics",
    "Quarterly Journal of Fake Finance",
    "Journal of Imaginary Agriculture",
    "Proceedings of the Unreal Symposium",
    "Journal of Dummy Urban Studies",
    "Review of Fabricated Security",
    "Quarterly Journal of Ghost Methods",
    "Journal of Placeholder Psychology",
    "Review of Invented Accounting",
)
PERCENTS = ("412%", "247 percent", "0.02%", "99.9%", "18.7%")
QUOTES = (
    '"Globalization always eliminates rural poverty within one fiscal year."',
    '"The unpublished trial proves that every student must cite five sources per paragraph."',
    '"Industrial policy is illegal in all developing economies after 1995."',
    '"The examiner secretly requires a 2:1 classification in the introduction."',
    '"A fictional sample of 12000 firms found zero inequality under openness."',
)


def build_hallucination_suite() -> list[tuple[str, str, bool]]:
    cases: list[tuple[str, str, bool]] = []
    # Legitimate reuse of diagnostic text must pass.
    cases.append(("Add a citation you have actually read.", ALLOWED, True))
    cases.append(("Rodrik (2011) already appears in the diagnostic.", ALLOWED + " Rodrik (2011)", True))
    cases.append(("Keep hedging: the draft appears thin on evidence.", ALLOWED, True))
    cases.append(("Point the student to their own paragraph 2.", ALLOWED, True))

    year = 2099
    for author in AUTHORS:
        for journal in JOURNALS:
            cases.append(
                (
                    f"According to {author} ({year}) in the {journal}, GDP rose 412%.",
                    ALLOWED,
                    False,
                )
            )
            cases.append(
                (
                    f"{author} (2099, p. 441) in the {journal} found 61 percent improvement.",
                    ALLOWED,
                    False,
                )
            )
            year = 2090 if year > 2105 else year + 1
        for pct in PERCENTS:
            cases.append((f"{author} (2099) reports {pct} growth.", ALLOWED, False))
        cases.append((f"See doi:10.9999/fake-{author.lower()}-xx", ALLOWED, False))
        cases.append((f"Your lecturer expects a citation to {author} (2099).", ALLOWED, False))
        cases.append((f"An unpublished study at {author} College used a fictional sample of 4400.", ALLOWED, False))
        cases.append((f"Quote: {QUOTES[0]} ({author}, 2099, p. 884).", ALLOWED, False))

    for quote in QUOTES:
        cases.append((f"Insert {quote}", ALLOWED, False))
    for journal in JOURNALS:
        cases.append((f"Publish this in the {journal} immediately.", ALLOWED, False))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[tuple[str, str, bool]] = []
    for item in cases:
        if item[0] in seen:
            continue
        seen.add(item[0])
        unique.append(item)
    return unique


def hallucination_escape_rate(cases: list[tuple[str, str, bool]] | None = None) -> dict:
    suite = cases or build_hallucination_suite()
    should_block = [(out, allowed) for out, allowed, ok in suite if not ok]
    escaped = 0
    for out, allowed in should_block:
        if allow_model_text(out, allowed):
            escaped += 1
    n = len(should_block)
    return {
        "n_should_block": n,
        "n_total": len(suite),
        "escaped": escaped,
        "escape_rate": (escaped / n) if n else 1.0,
        "target": 0.005,
        "pass_target": n >= 1000 and (escaped / n if n else 1) < 0.005,
    }

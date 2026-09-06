from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.services.analysis.citations import analyze_citations
from app.services.analysis.engine import run_analysis
from app.services.analysis.question import COMMANDS, analyze_question
from app.services.documents.extractor import ExtractedDocument, ExtractedParagraph

BASELINE_PATH = Path(__file__).with_name("eval_baseline.json")


@dataclass
class Metric:
    name: str
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    support: int

    def to_dict(self) -> dict:
        return asdict(self)


TOPICS = [
    "the effects of globalization on developing economies",
    "the role of monetary policy in inflation targeting",
    "climate change and food security in West Africa",
    "social media and political participation",
    "rural-urban migration in Ghana",
    "industrial policy in East Asia",
    "the impact of colonial education on language policy",
    "gender and access to higher education",
    "corruption and public service delivery in Nigeria",
    "renewable energy transitions in Kenya",
]


def question_gold() -> list[tuple[str, set[str]]]:
    cases: list[tuple[str, set[str]]] = []
    stems = [
        "{cmd} {topic}.",
        "{cmd} {topic} using relevant examples.",
        "In no more than 2000 words, {cmd} {topic}.",
        "{cmd} {topic} with reference to scholarly sources.",
    ]
    for cmd in COMMANDS:
        expected = {cmd}
        for topic in TOPICS:
            for stem in stems:
                cases.append((stem.format(cmd=cmd.capitalize(), topic=topic), expected))
    return cases


def thesis_gold() -> list[tuple[str, str, str]]:
    """(question, draft, expected strength). Expert-constructed labels."""
    q = "Compare and evaluate the effects of globalization on developing economies."
    strong = [
        "This essay argues that industrial policy, not openness alone, determines development outcomes.",
        "Globalization should be judged by distribution and capability, because average GDP conceals widening inequality.",
        "I contend that trade openness succeeds only when states can upgrade industry rather than specialise in commodities.",
        "The central claim is that openness is limited unless complementary industrial policy is present.",
        "Developing economies benefit from globalization only insofar as policy capability outweighs commodity dependence.",
    ]
    weak = [
        "Globalization is an interesting topic that many scholars have discussed.",
        "This essay is about globalization and developing economies.",
        "This paper will discuss some effects of trade.",
        "I will talk about climate change and some related issues.",
        "The topic of this assignment is international trade.",
    ]
    missing = [
        "Trade has increased in recent decades across several regions.",
        "Many countries export more than they did in 1980.",
        "There are several definitions of globalization in the literature.",
        "The next section reviews selected data sources.",
        "Paragraph one introduces background material only.",
    ]
    cases = []
    for text in strong:
        cases.append((q, text, "strong"))
    for text in weak:
        cases.append((q, text, "weak"))
    for text in missing:
        cases.append((q, text, "missing"))
    # Expand with topic variants while keeping the same label logic.
    for topic in TOPICS:
        q2 = f"Evaluate {topic}."
        cases.append((q2, f"This essay argues that policy design, not description, determines outcomes in {topic}.", "strong"))
        cases.append((q2, f"This essay is about {topic}.", "weak"))
        cases.append((q2, f"Background on {topic} is presented first.", "missing"))
    return cases


def citation_gold() -> list[tuple[str, int, int]]:
    """(text, expected_in_text, expected_references)."""
    cases = [
        ("Rodrik (2011) argues that policy capability matters.", 1, 0),
        ("Some people say this is true.", 0, 0),
        ("According to Sen (1999) and Stiglitz (2002), institutions shape outcomes.", 2, 0),
        ("Trade rose after liberalisation (Rodrik, 2011).", 1, 0),
        ("Acemoglu and Robinson (2012) emphasise institutions.", 1, 0),
        ("See also recent commentary without a year.", 0, 0),
        (
            "Capability matters (Rodrik, 2011).\n\nReferences\nRodrik, D. (2011). The globalization paradox. W. W. Norton.",
            1,
            1,
        ),
    ]
    authors = ["Sen", "Rodrik", "Stiglitz", "Acemoglu", "Mkandawire", "Chang", "Nkrumah", "Ake"]
    years = [1999, 2002, 2007, 2011, 2012, 2015, 2018, 2020]
    for author, year in zip(authors, years):
        cases.append((f"{author} ({year}) discusses institutions and development.", 1, 0))
        cases.append((f"The claim is contested ({author}, {year}).", 1, 0))
        cases.append((f"{author} writes without a parenthetical year in this sentence.", 0, 0))
    return cases


def argument_gold() -> list[tuple[str, bool]]:
    """True if the paragraph contains a claim plus reasoning, not mere description."""
    reasoned = [
        "Export growth rose, but inequality widened because upgrading did not follow liberalisation.\n\nTherefore openness alone does not determine outcomes; policy capability mediates the effect.",
        "The comparison shows mixed results. This suggests that commodity exporters remain vulnerable unless industrial policy is present.",
        "Capability mediates trade effects. Consequently, liberalisation without upgrading is an incomplete explanation.",
    ]
    descriptive = [
        "Exports increased from 1990 to 2010 in several countries.",
        "There are many books about trade policy.",
        "The next chapter lists definitions of globalization.",
    ]
    cases = [(t, True) for t in reasoned] + [(t, False) for t in descriptive]
    for topic in TOPICS:
        cases.append((f"Therefore {topic} cannot be reduced to a single cause.", True))
        cases.append((f"There is a literature on {topic}.", False))
    return cases


def evidence_gold() -> list[tuple[str, bool]]:
    """True if a specific claim appears to need a citation."""
    needs = [
        "GDP grew by 7 percent after liberalisation.",
        "A study found that inequality widened in commodity exporters.",
        "Research indicates that industrial policy raised productivity.",
    ]
    ok = [
        "This paragraph explains the meaning of evaluation as judgement against criteria.",
        "A thesis should be contestable rather than a topic label.",
        "The command word compare requires similarities and differences.",
    ]
    cases = [(t, True) for t in needs] + [(t, False) for t in ok]
    for topic in TOPICS:
        cases.append((f"Statistics show rapid change in {topic}.", True))
        cases.append((f"Evaluation of {topic} requires criteria, not only description.", False))
    return cases


def rubric_gold() -> list[tuple[list[dict], str, list[str]]]:
    criteria = [
        {"name": "Thesis", "weight_percent": 20, "max_points": 20},
        {"name": "Evidence", "weight_percent": 30, "max_points": 30},
        {"name": "Structure", "weight_percent": 20, "max_points": 20},
        {"name": "Citations", "weight_percent": 15, "max_points": 15},
        {"name": "Evaluation", "weight_percent": 15, "max_points": 15},
    ]
    drafts = [
        (
            "This essay argues that industrial policy determines outcomes. Evidence from Rodrik (2011) supports the claim. "
            "However, commodity exporters show limits. Therefore the judgement is mixed.\n\nReferences\nRodrik, D. (2011). The globalization paradox. Norton.",
            ["Thesis", "Evidence", "Citations", "Evaluation"],
        ),
        ("Globalization is an interesting topic.", []),
    ]
    cases = []
    for draft, expected in drafts:
        cases.append((criteria, draft, expected))
    for topic in TOPICS:
        cases.append(
            (
                criteria,
                f"This essay argues that evaluation of {topic} requires criteria because description is insufficient (Rodrik, 2011).",
                ["Thesis", "Evidence"],
            )
        )
    return cases


def evaluate_question_analyzer() -> Metric:
    tp = fp = fn = 0
    cases = question_gold()
    for text, expected in cases:
        parsed = {w.lower() for w in analyze_question(text).command_words}
        expected_l = {w.lower() for w in expected}
        tp += len(parsed & expected_l)
        fp += len(parsed - expected_l)
        fn += len(expected_l - parsed)
    return _metric("question_analyzer", tp, fp, fn, len(cases))


def evaluate_thesis_analyzer() -> Metric:
    tp = fp = fn = 0
    cases = thesis_gold()
    for question, draft, expected in cases:
        result = run_analysis(_doc(draft), question)
        predicted = result.thesis.get("strength") or "missing"
        if expected == "strong":
            if predicted == "strong":
                tp += 1
            else:
                fn += 1
        else:
            if predicted == "strong":
                fp += 1
            elif predicted == expected:
                tp += 1
            else:
                # weak vs missing is a near miss: count as FN for the expected class
                fn += 1
    return _metric("thesis_analyzer", tp, fp, fn, len(cases))


def evaluate_citation_extractor() -> Metric:
    tp = fp = fn = 0
    for text, expected_cites, expected_refs in citation_gold():
        report = analyze_citations(text, _paragraphs(text), "apa7")
        found_c = len(report.citations)
        found_r = len(report.references)
        tp += min(found_c, expected_cites) + min(found_r, expected_refs)
        fp += max(0, found_c - expected_cites) + max(0, found_r - expected_refs)
        fn += max(0, expected_cites - found_c) + max(0, expected_refs - found_r)
    return _metric("citation_extractor", tp, fp, fn, len(citation_gold()))


def evaluate_argument_analyzer() -> Metric:
    tp = fp = fn = 0
    for text, reasoned in argument_gold():
        result = run_analysis(_doc(text), "Evaluate the claim in the paragraph.")
        arg = next((s.score for s in result.scores if s.category == "argument"), 50)
        predicted = arg >= 60
        if reasoned and predicted:
            tp += 1
        elif reasoned and not predicted:
            fn += 1
        elif not reasoned and not predicted:
            tp += 1
        else:
            fp += 1
    return _metric("argument_analyzer", tp, fp, fn, len(argument_gold()))


def evaluate_evidence_analyzer() -> Metric:
    tp = fp = fn = 0
    for text, needs_cite in evidence_gold():
        result = run_analysis(_doc(text), "Assess the use of evidence in this paragraph.")
        flagged = any(f.category == "evidence" for f in result.findings)
        if needs_cite and flagged:
            tp += 1
        elif needs_cite and not flagged:
            fn += 1
        elif not needs_cite and not flagged:
            tp += 1
        else:
            fp += 1
    return _metric("evidence_analyzer", tp, fp, fn, len(evidence_gold()))


def evaluate_rubric_checker() -> Metric:
    tp = fp = fn = 0
    for criteria, draft, expected in rubric_gold():
        result = run_analysis(_doc(draft), "Evaluate the assignment against the rubric.", rubric_criteria=criteria)
        names = {c.get("name") for c in (result.rubric.get("criteria") or []) if c.get("awarded", 0) > 0}
        if not names and result.rubric:
            names = {c.get("name") for c in result.rubric.get("criteria") or [] if (c.get("score") or c.get("awarded") or 0)}
        expected_s = set(expected)
        if not names:
            # Fall back: thesis/evidence scores proxy coverage
            names = set()
            for score in result.scores:
                if score.category == "thesis" and score.score >= 70:
                    names.add("Thesis")
                if score.category == "evidence" and score.score >= 50:
                    names.add("Evidence")
                if score.category == "citations" and score.score >= 50:
                    names.add("Citations")
                if score.category == "relevance" and score.score >= 60:
                    names.add("Evaluation")
        tp += len(names & expected_s)
        fp += len(names - expected_s)
        fn += len(expected_s - names)
    return _metric("rubric_checker", tp, fp, fn, len(rubric_gold()))


def run_all() -> list[Metric]:
    return [
        evaluate_question_analyzer(),
        evaluate_thesis_analyzer(),
        evaluate_citation_extractor(),
        evaluate_argument_analyzer(),
        evaluate_evidence_analyzer(),
        evaluate_rubric_checker(),
    ]


def suite_sizes() -> dict[str, int]:
    return {
        "question": len(question_gold()),
        "thesis": len(thesis_gold()),
        "citation": len(citation_gold()),
        "argument": len(argument_gold()),
        "evidence": len(evidence_gold()),
        "rubric": len(rubric_gold()),
        "total": (
            len(question_gold())
            + len(thesis_gold())
            + len(citation_gold())
            + len(argument_gold())
            + len(evidence_gold())
            + len(rubric_gold())
        ),
    }


def load_baseline() -> dict[str, float]:
    if not BASELINE_PATH.exists():
        return {}
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def write_baseline(metrics: list[Metric]) -> None:
    BASELINE_PATH.write_text(json.dumps({m.name: round(m.f1, 4) for m in metrics}, indent=2), encoding="utf-8")


def _doc(text: str) -> ExtractedDocument:
    paragraphs = _paragraphs(text)
    words = len(text.split())
    return ExtractedDocument(
        text=text,
        normalized_text=text,
        paragraphs=paragraphs,
        sections=[],
        word_count=words,
        word_count_excl_references=words,
        word_count_excl_headings=words,
        paragraph_count=len(paragraphs),
        sentence_count=max(1, text.count(".") + text.count("?")),
        page_count=1,
        language="en",
    )


def _paragraphs(text: str) -> list[ExtractedParagraph]:
    blocks = [b.strip() for b in text.split("\n") if b.strip()]
    if not blocks:
        blocks = [text]
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


def _metric(name: str, tp: int, fp: int, fn: int, support: int) -> Metric:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return Metric(name, precision, recall, f1, tp, fp, fn, support)

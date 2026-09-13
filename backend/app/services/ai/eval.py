from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.services.analysis.citations import analyze_citations
from app.services.ai.agreement import agreement_report, load_reviews
from app.services.ai.hallucination import allow_model_text
from app.services.ai.calibration import hard_label_calibration
from app.services.ai.citation_corpus import parser_robustness
from app.services.ai.hallucination_suite import hallucination_escape_rate
from app.services.ai.heldout import (
    ARGUMENT_HELDOUT,
    CITATION_HELDOUT,
    COACH_REFUSAL,
    EVIDENCE_HELDOUT,
    HALLUCINATION_CASES,
    QUESTION_HELDOUT,
    THESIS_HELDOUT,
)
from app.services.ai.live_eval import live_eval_status
from app.services.ai.prompt_registry import registry_report
from app.services.ai.stats import wilson_interval
from app.services.analysis.classifiers import (
    argument_structure,
    classify_evidence,
    classify_thesis,
    has_reasoned_argument,
    needs_citation,
    rubric_covered,
)
from app.services.analysis.question import COMMANDS, analyze_question
from app.services.analysis.verify_sources import verify_reference
from app.services.documents.extractor import ExtractedParagraph

BASELINE_PATH = Path(__file__).with_name("eval_baseline.json")

CERT_MIN_N = {
    "heldout_question": 1000,
    "heldout_thesis": 1000,
    "heldout_argument": 1000,
    "heldout_evidence": 1000,
    "heldout_citation": 2000,
}
CERT_F1 = 0.98
CIRCULAR_SUITES = {
    "question_analyzer",
    "thesis_analyzer",
    "citation_extractor",
    "argument_analyzer",
    "evidence_analyzer",
    "rubric_checker",
}

LEVELS = ("undergraduate", "postgraduate", "masters", "phd")
DISCIPLINES = {
    "humanities": [
        "the impact of colonial education on language policy",
        "gender and access to higher education",
        "narrative form in postcolonial novels",
        "memory and testimony in oral history",
        "secularism and public reason",
        "translation ethics in world literature",
        "canon formation in African philosophy",
        "rhetoric of human rights declarations",
    ],
    "business": [
        "corporate governance after financial scandal",
        "platform competition in digital markets",
        "family-firm succession in emerging economies",
        "stakeholder theory in extractive industries",
        "pricing power in concentrated retail markets",
        "board independence and earnings quality",
        "entrepreneurial finance after crisis",
        "supply-chain resilience in manufacturing",
    ],
    "engineering": [
        "renewable energy transitions in Kenya",
        "safety cases for autonomous vehicles",
        "reliability of distributed sensor networks",
        "lifecycle cost of rural electrification",
        "cyber-physical risk in industrial control",
        "materials substitution in lightweight design",
        "failure modes in prestressed concrete",
        "thermal efficiency of district heating",
    ],
    "healthcare": [
        "antimicrobial stewardship in district hospitals",
        "primary-care access after user-fee reform",
        "informed consent in paediatric trials",
        "workforce retention in rural clinics",
        "diagnostic delay in tuberculosis programmes",
        "equity of vaccine allocation rules",
        "continuity of care for chronic disease",
        "triage protocols under capacity strain",
    ],
    "social_science": [
        "social media and political participation",
        "trust in public institutions after protest",
        "urban housing and informal tenure",
        "policing and procedural justice",
        "migration and social cohesion",
        "welfare conditionality and stigma",
        "civic education and turnout",
        "community health worker programmes",
    ],
    "economics": [
        "the effects of globalization on developing economies",
        "the role of monetary policy in inflation targeting",
        "industrial policy in East Asia",
        "corruption and public service delivery in Nigeria",
        "rural-urban migration in Ghana",
        "climate change and food security in West Africa",
        "informal employment and tax capacity",
        "exchange-rate pass-through to consumer prices",
    ],
}
TOPICS = [topic for topics in DISCIPLINES.values() for topic in topics]


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
    confusion: dict = field(default_factory=dict)
    source: str = "circular"
    precision_ci95: list[float] = field(default_factory=lambda: [0.0, 0.0])
    recall_ci95: list[float] = field(default_factory=lambda: [0.0, 0.0])
    f1_ci95: list[float] = field(default_factory=lambda: [0.0, 0.0])
    certifiable: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def question_gold() -> list[tuple[str, set[str]]]:
    cases: list[tuple[str, set[str]]] = []
    stems = [
        "{cmd} {topic}.",
        "In no more than 2000 words, {cmd} {topic}.",
        "{cmd} {topic} using relevant examples.",
    ]
    for cmd in COMMANDS:
        expected = {cmd}
        for topic in TOPICS:
            for stem in stems:
                cases.append((stem.format(cmd=cmd.capitalize(), topic=topic), expected))
    return cases


def thesis_gold() -> list[tuple[str, str, str]]:
    """Expert-constructed labels from writing-centre rules, not model self-agreement.

    strong: contestable answer to the question, or an explicit thesis marker.
    weak: topic announcement without a contestable claim.
    missing: background or description with no position.
    """
    cases: list[tuple[str, str, str]] = []
    for level in LEVELS:
        for discipline, topics in DISCIPLINES.items():
            for topic in topics:
                q = f"Evaluate {topic}."
                cases.extend(
                    (
                        (
                            q,
                            (
                                f"This essay argues that policy design, not description, determines outcomes in {topic} "
                                f"at {level} level."
                            ),
                            "strong",
                        ),
                        (
                            q,
                            (
                                f"I contend that {topic} should be judged by distribution and capability "
                                f"because averages conceal inequality."
                            ),
                            "strong",
                        ),
                        (
                            q,
                            (
                                f"The central claim is that {topic} is limited unless complementary institutions "
                                f"are present."
                            ),
                            "strong",
                        ),
                        (
                            q,
                            f"This dissertation argues that {topic} succeeds only insofar as institutions outweigh commodity dependence.",
                            "strong",
                        ),
                        (
                            q,
                            f"It will be argued that {topic} must be judged by capability rather than average growth.",
                            "strong",
                        ),
                        (
                            q,
                            f"The main argument is that {topic} fails when complementary industrial policy is absent.",
                            "strong",
                        ),
                        (
                            q,
                            f"This study argues that {topic} depends on state capability rather than openness alone.",
                            "strong",
                        ),
                        (q, f"This essay is about {topic}.", "weak"),
                        (q, f"This paper will discuss some aspects of {topic}.", "weak"),
                        (q, f"{topic.capitalize()} is an interesting topic that many scholars have discussed.", "weak"),
                        (q, f"This assignment will look at {topic} in general terms.", "weak"),
                        (q, f"I will write about {topic} and related issues.", "weak"),
                        (q, f"The topic of this paper is {topic}.", "weak"),
                        (q, f"Background on {topic} is presented first.", "missing"),
                        (q, f"The next section reviews selected data sources for {discipline} readers.", "missing"),
                        (q, f"Many countries export more than they did in 1980 around {topic}.", "missing"),
                        (q, f"There are several definitions used when introducing {topic}.", "missing"),
                        (q, f"Paragraph one introduces selected facts about {topic} only.", "missing"),
                        (
                            q,
                            f"This paper argues that {topic} should be treated as a capability problem, not a volume problem.",
                            "strong",
                        ),
                        (q, f"This article will explore {topic} without taking a position.", "weak"),
                        (q, f"Selected tables for {topic} appear before any claim is made.", "missing"),
                    )
                )
    return cases


def citation_gold() -> list[tuple[str, int, int]]:
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
    authors = [
        "Sen",
        "Rodrik",
        "Stiglitz",
        "Acemoglu",
        "Mkandawire",
        "Chang",
        "Nkrumah",
        "Ake",
        "Fanon",
        "Mbembe",
        "Ostrom",
        "North",
        "Khan",
        "Evans",
        "Wade",
        "Amsden",
    ]
    years = [1999, 2002, 2007, 2011, 2012, 2015, 2018, 2020, 1986, 2001, 1990, 1991, 2010, 1995, 2004, 1989]
    for author, year in zip(authors, years):
        cases.append((f"{author} ({year}) discusses institutions and development.", 1, 0))
        cases.append((f"The claim is contested ({author}, {year}).", 1, 0))
        cases.append((f"{author} writes without a parenthetical year in this sentence.", 0, 0))
    return cases


def argument_gold() -> list[tuple[str, bool]]:
    """True if the paragraph contains a claim plus a reason or consequence marker."""
    cases: list[tuple[str, bool]] = []
    for level in LEVELS:
        for topics in DISCIPLINES.values():
            for topic in topics:
                cases.append(
                    (
                        (
                            f"Export growth rose, but inequality widened because upgrading did not follow "
                            f"liberalisation in {topic}. Therefore openness alone does not determine {level} outcomes."
                        ),
                        True,
                    )
                )
                cases.append((f"This shows that {topic} cannot be reduced to a single cause.", True))
                cases.append((f"Consequently, {topic} requires criteria rather than description.", True))
                cases.append((f"It is clear that {topic} depends on complementary institutions.", True))
                cases.append((f"This suggests that {topic} is incomplete without institutional analysis.", True))
                cases.append((f"Thus {topic} cannot be treated as an automatic outcome of liberalisation.", True))
                cases.append((f"As a result, {topic} should be explained through capability, not volume.", True))
                cases.append((f"This means {topic} is a mediated process rather than a single shock.", True))
                cases.append((f"Therefore {topic} cannot be reduced to a single cause.", True))
                cases.append((f"This demonstrates that {topic} is institutionally mediated.", True))
                cases.append((f"There is a literature on {topic}.", False))
                cases.append((f"The next chapter lists definitions of {topic}.", False))
                cases.append((f"There are many books about {topic} at {level} level.", False))
                cases.append((f"This section reviews background material on {topic}.", False))
                cases.append((f"Background material on {topic} is arranged chronologically.", False))
                cases.append((f"The following pages list key terms used in {topic}.", False))
                cases.append((f"There are several handbooks that mention {topic}.", False))
                cases.append((f"The opening pages catalogue titles related to {topic}.", False))
                cases.append((f"A list of dates follows the introduction of {topic}.", False))
    return cases


def evidence_gold() -> list[tuple[str, bool]]:
    """True if a specific empirical claim appears without a citation."""
    cases: list[tuple[str, bool]] = []
    for level in LEVELS:
        for topics in DISCIPLINES.values():
            for topic in topics:
                cases.append((f"GDP grew by 7 percent after liberalisation in {topic} at {level} level.", True))
                cases.append((f"A study found that inequality widened when {topic} was treated as automatic.", True))
                cases.append((f"Research indicates that industrial policy raised productivity around {topic}.", True))
                cases.append((f"Statistics show rapid change in {topic}.", True))
                cases.append((f"Research suggests that {topic} is mediated by institutions.", True))
                cases.append((f"Unemployment rose after the reform discussed in {topic}.", True))
                cases.append((f"Inflation reached 12 percent during the episode linked to {topic}.", True))
                cases.append((f"A study found mixed results for {topic} after liberalisation.", True))
                cases.append((f"Research shows rapid change when {topic} is left ungoverned.", True))
                cases.append((f"Evaluation of {topic} requires criteria, not only description.", False))
                cases.append((f"A thesis on {topic} should be contestable rather than a topic label.", False))
                cases.append((f"The command word compare requires similarities and differences about {topic}.", False))
                cases.append((f"This paragraph explains the meaning of evaluation as judgement against criteria.", False))
                cases.append((f"GDP grew by 7 percent after liberalisation (Rodrik, 2011).", False))
                cases.append((f"A study found mixed results (Sen, 1999).", False))
    return cases


def rubric_gold() -> list[tuple[list[dict], dict[str, int], list[str]]]:
    criteria = [
        {"name": "Thesis", "weight_percent": 20, "max_points": 20},
        {"name": "Evidence", "weight_percent": 30, "max_points": 30},
        {"name": "Structure", "weight_percent": 20, "max_points": 20},
        {"name": "Citations", "weight_percent": 15, "max_points": 15},
        {"name": "Evaluation", "weight_percent": 15, "max_points": 15},
    ]
    cases: list[tuple[list[dict], dict[str, int], list[str]]] = []
    strong_scores = {
        "thesis": 82,
        "evidence": 78,
        "structure": 74,
        "citations": 80,
        "relevance": 76,
        "argument": 70,
        "academic_writing": 68,
        "grammar": 70,
        "references": 60,
    }
    weak_scores = {
        "thesis": 30,
        "evidence": 28,
        "structure": 40,
        "citations": 20,
        "relevance": 32,
        "argument": 34,
        "academic_writing": 40,
        "grammar": 50,
        "references": 20,
    }
    mixed_scores = {
        "thesis": 80,
        "evidence": 72,
        "structure": 40,
        "citations": 30,
        "relevance": 70,
        "argument": 66,
        "academic_writing": 60,
        "grammar": 60,
        "references": 30,
    }
    for _level in LEVELS:
        for _discipline in DISCIPLINES:
            cases.append((criteria, strong_scores, ["Thesis", "Evidence", "Structure", "Citations", "Evaluation"]))
            cases.append((criteria, weak_scores, []))
            cases.append((criteria, mixed_scores, ["Thesis", "Evidence", "Evaluation"]))
            cases.append(
                (
                    [
                        {"name": "Critical analysis", "weight_percent": 40, "max_points": 40},
                        {"name": "Referencing", "weight_percent": 30, "max_points": 30},
                        {"name": "Judgement", "weight_percent": 30, "max_points": 30},
                    ],
                    {"argument": 70, "citations": 68, "relevance": 72, "academic_writing": 40},
                    ["Critical analysis", "Referencing", "Judgement"],
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
    return _metric("question_analyzer", tp, fp, fn, len(cases), source="circular")


def evaluate_thesis_analyzer() -> Metric:
    labels = ("strong", "weak", "missing")
    matrix = {exp: {pred: 0 for pred in labels} for exp in labels}
    tp = fp = fn = 0
    cases = thesis_gold()
    for question, draft, expected in cases:
        predicted = classify_thesis(draft, question)
        matrix[expected][predicted] += 1
        if predicted == expected:
            tp += 1
        else:
            fp += 1
            fn += 1
    return _metric("thesis_analyzer", tp, fp, fn, len(cases), matrix, source="circular")


def evaluate_citation_extractor() -> Metric:
    tp = fp = fn = 0
    for text, expected_cites, expected_refs in citation_gold():
        report = analyze_citations(text, _paragraphs(text), "apa7")
        found_c = len(report.citations)
        found_r = len(report.references)
        tp += min(found_c, expected_cites) + min(found_r, expected_refs)
        fp += max(0, found_c - expected_cites) + max(0, found_r - expected_refs)
        fn += max(0, expected_cites - found_c) + max(0, expected_refs - found_r)
    return _metric("citation_extractor", tp, fp, fn, len(citation_gold()), source="circular")


def evaluate_argument_analyzer() -> Metric:
    tp = fp = fn = tn = 0
    for text, reasoned in argument_gold():
        predicted = has_reasoned_argument(text)
        if reasoned and predicted:
            tp += 1
        elif reasoned and not predicted:
            fn += 1
        elif not reasoned and not predicted:
            tn += 1
        else:
            fp += 1
    return _metric(
        "argument_analyzer",
        tp,
        fp,
        fn,
        len(argument_gold()),
        {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        source="circular",
    )


def evaluate_evidence_analyzer() -> Metric:
    tp = fp = fn = tn = 0
    for text, needs_cite in evidence_gold():
        predicted = needs_citation(text)
        if needs_cite and predicted:
            tp += 1
        elif needs_cite and not predicted:
            fn += 1
        elif not needs_cite and not predicted:
            tn += 1
        else:
            fp += 1
    return _metric(
        "evidence_analyzer",
        tp,
        fp,
        fn,
        len(evidence_gold()),
        {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        source="circular",
    )


def evaluate_rubric_checker() -> Metric:
    tp = fp = fn = 0
    for criteria, scores, expected in rubric_gold():
        names = rubric_covered(criteria, scores)
        expected_s = set(expected)
        tp += len(names & expected_s)
        fp += len(names - expected_s)
        fn += len(expected_s - names)
    return _metric("rubric_checker", tp, fp, fn, len(rubric_gold()), source="circular")


def evaluate_heldout_question() -> Metric:
    tp = fp = fn = 0
    for text, expected in QUESTION_HELDOUT:
        parsed = {w.lower() for w in analyze_question(text).command_words}
        expected_l = {w.lower() for w in expected}
        tp += len(parsed & expected_l)
        fp += len(parsed - expected_l)
        fn += len(expected_l - parsed)
    return _metric("heldout_question", tp, fp, fn, len(QUESTION_HELDOUT), source="heldout")


def evaluate_heldout_thesis() -> Metric:
    tp = fp = fn = 0
    for question, draft, expected in THESIS_HELDOUT:
        predicted = classify_thesis(draft, question)
        if predicted == expected:
            tp += 1
        else:
            fp += 1
            fn += 1
    return _metric("heldout_thesis", tp, fp, fn, len(THESIS_HELDOUT), source="heldout")


def evaluate_heldout_argument() -> Metric:
    tp = fp = fn = tn = 0
    for text, reasoned in ARGUMENT_HELDOUT:
        predicted = has_reasoned_argument(text)
        if reasoned and predicted:
            tp += 1
        elif reasoned and not predicted:
            fn += 1
        elif not reasoned and not predicted:
            tn += 1
        else:
            fp += 1
    return _metric("heldout_argument", tp, fp, fn, len(ARGUMENT_HELDOUT), {"tp": tp, "fp": fp, "fn": fn, "tn": tn}, source="heldout")


def evaluate_heldout_evidence() -> Metric:
    labels = ("supported", "needs_citation", "potentially_unsupported", "cannot_determine")
    matrix = {exp: {pred: 0 for pred in labels} for exp in labels}
    tp = fp = fn = 0
    for text, expected in EVIDENCE_HELDOUT:
        predicted = classify_evidence(text)
        matrix[expected][predicted] += 1
        if predicted == expected:
            tp += 1
        else:
            fp += 1
            fn += 1
    return _metric("heldout_evidence", tp, fp, fn, len(EVIDENCE_HELDOUT), matrix, source="heldout")


def evaluate_heldout_citation() -> Metric:
    tp = fp = fn = 0
    for text, style, expected_cites, expected_refs in CITATION_HELDOUT:
        report = analyze_citations(text, _paragraphs(text), style)
        found_c = len(report.citations)
        found_r = len(report.references)
        tp += min(found_c, expected_cites) + min(found_r, expected_refs)
        fp += max(0, found_c - expected_cites) + max(0, found_r - expected_refs)
        fn += max(0, expected_cites - found_c) + max(0, expected_refs - found_r)
    return _metric("heldout_citation", tp, fp, fn, len(CITATION_HELDOUT), source="heldout")


def evaluate_hallucination_guard() -> Metric:
    tp = fp = fn = tn = 0
    for output, allowed, should_pass in HALLUCINATION_CASES:
        allowed_ok = allow_model_text(output, allowed)
        if should_pass and allowed_ok:
            tp += 1
        elif should_pass and not allowed_ok:
            fn += 1
        elif not should_pass and not allowed_ok:
            tn += 1
        else:
            fp += 1
    return _metric(
        "hallucination_guard",
        tp,
        fp,
        fn,
        len(HALLUCINATION_CASES),
        {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        source="heldout",
        notes="n=4 unit cases. Not the 1000-case red-team suite.",
    )


def evaluate_coach_refusal() -> Metric:
    from app.services.ai.enhance import _heuristic_coach

    tp = fp = fn = 0
    for question, needle in COACH_REFUSAL:
        answer = _heuristic_coach(question, "context")
        if needle == "will not":
            hit = "will not" in answer.lower() or "not generate" in answer.lower() or "not write" in answer.lower()
        else:
            hit = needle.lower() in answer.lower()
        if hit:
            tp += 1
        else:
            fn += 1
    return _metric("coach_refusal", tp, fp, fn, len(COACH_REFUSAL), source="heldout")


def evaluate_argument_coverage() -> dict:
    rows = []
    for text, reasoned in ARGUMENT_HELDOUT:
        flags = argument_structure(text)
        rows.append({"reasoned_gold": reasoned, **flags})
    n = len(rows)
    return {
        "n": n,
        "claim_rate": (sum(1 for r in rows if r["claim"]) / n) if n else 0.0,
        "reasoning_rate": (sum(1 for r in rows if r["reasoning"]) / n) if n else 0.0,
        "counterargument_rate": (sum(1 for r in rows if r["counterargument"]) / n) if n else 0.0,
        "rebuttal_rate": (sum(1 for r in rows if r["rebuttal"]) / n) if n else 0.0,
        "logical_gap_rate": (sum(1 for r in rows if r["logical_gap"]) / n) if n else 0.0,
        "note": "Coverage of heuristic flags on held-out paragraphs. Not relationship-accuracy gold.",
    }


def evaluate_verification_contract() -> dict:
    empty = verify_reference()
    return {
        "empty_status": empty.status,
        "never_invents_on_empty": empty.status == "could_not_verify",
        "precision": None,
        "recall": None,
        "n_labeled": 0,
        "note": "Live Crossref/OpenAlex/Semantic Scholar precision is unmeasured. Empty lookup is not verified.",
    }


def heldout_hard_correctness() -> list[bool]:
    correct: list[bool] = []
    for question, draft, expected in THESIS_HELDOUT:
        correct.append(classify_thesis(draft, question) == expected)
    for text, reasoned in ARGUMENT_HELDOUT:
        correct.append(has_reasoned_argument(text) is reasoned)
    for text, expected in EVIDENCE_HELDOUT:
        correct.append(classify_evidence(text) == expected)
    return correct


def certification_verdict(metrics: list[Metric], extras: dict) -> dict:
    by_name = {m.name: m for m in metrics}
    gates = []
    for name, min_n in CERT_MIN_N.items():
        m = by_name.get(name)
        measured_n = m.support if m else 0
        f1 = m.f1 if m else 0.0
        f1_lo = m.f1_ci95[0] if m else 0.0
        ok = bool(m and m.source == "heldout" and measured_n >= min_n and f1_lo >= CERT_F1)
        gates.append(
            {
                "gate": name,
                "required_n": min_n,
                "measured_n": measured_n,
                "required_f1_ci_low": CERT_F1,
                "f1": f1,
                "f1_ci_low": f1_lo,
                "pass": ok,
            }
        )
    hall = extras.get("hallucination_redteam") or {}
    hall_ok = bool(hall.get("pass_target"))
    gates.append(
        {
            "gate": "hallucination_escape",
            "required": "<0.005 on n>=1000 red-team block cases",
            "measured": hall.get("escape_rate"),
            "n": hall.get("n_should_block"),
            "pass": hall_ok,
        }
    )
    agree = extras.get("reviewer_agreement") or {}
    gates.append(
        {
            "gate": "reviewer_agreement",
            "required": "dual lecturer labels",
            "measured_n": agree.get("n", 0),
            "pass": False,
        }
    )
    ver = extras.get("verification") or {}
    gates.append(
        {
            "gate": "reference_verification_precision",
            "required": 0.98,
            "measured": ver.get("precision"),
            "pass": False,
        }
    )
    live = extras.get("live_llm") or {}
    gates.append(
        {
            "gate": "schema_compliance_live",
            "required": 0.999,
            "measured": None,
            "n_run": live.get("n_run", 0),
            "pass": False,
        }
    )
    return {
        "claim_98": False,
        "any_gate_pass_for_98": any(g.get("pass") and g.get("gate", "").startswith("heldout") for g in gates),
        "certified": False,
        "gates": gates,
        "reason": (
            "98% AI quality is not certified. Held-out n is below the independent-label floors, "
            "template suites are circular, reviewer labels are absent, live LLM eval was not run, "
            "and reference-verification precision is unmeasured."
        ),
    }


def extras_bundle() -> dict:
    return {
        "hallucination_redteam": hallucination_escape_rate(),
        "reviewer_agreement": agreement_report(load_reviews()),
        "verification": evaluate_verification_contract(),
        "citation_parser_robustness": parser_robustness(),
        "argument_coverage": evaluate_argument_coverage(),
        "live_llm": live_eval_status(),
        "prompt_registry": registry_report(),
        "calibration": hard_label_calibration(heldout_hard_correctness()),
    }


def run_all() -> list[Metric]:
    return [
        evaluate_question_analyzer(),
        evaluate_thesis_analyzer(),
        evaluate_citation_extractor(),
        evaluate_argument_analyzer(),
        evaluate_evidence_analyzer(),
        evaluate_rubric_checker(),
        evaluate_heldout_question(),
        evaluate_heldout_thesis(),
        evaluate_heldout_argument(),
        evaluate_heldout_evidence(),
        evaluate_heldout_citation(),
        evaluate_hallucination_guard(),
        evaluate_coach_refusal(),
    ]


def write_report(metrics: list[Metric], path: Path | None = None) -> Path:
    dest = path or Path(__file__).with_name("eval_report.json")
    extras = extras_bundle()
    dest.write_text(
        json.dumps(
            {
                "suites": {m.name: m.to_dict() for m in metrics},
                "sizes": suite_sizes(),
                "circular_suites": sorted(CIRCULAR_SUITES),
                **extras,
                "certification": certification_verdict(metrics, extras),
                "note": (
                    "Template gold is circular (same rules generate labels and classifiers). "
                    "Held-out cases are independent expert-constructed examples, not lecturer-reviewed gold. "
                    "Do not claim 98% AI quality from this report."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return dest


def suite_sizes() -> dict[str, int]:
    return {
        "question": len(question_gold()),
        "thesis": len(thesis_gold()),
        "citation": len(citation_gold()),
        "argument": len(argument_gold()),
        "evidence": len(evidence_gold()),
        "rubric": len(rubric_gold()),
        "heldout_question": len(QUESTION_HELDOUT),
        "heldout_thesis": len(THESIS_HELDOUT),
        "heldout_argument": len(ARGUMENT_HELDOUT),
        "heldout_evidence": len(EVIDENCE_HELDOUT),
        "heldout_citation": len(CITATION_HELDOUT),
        "heldout": (
            len(QUESTION_HELDOUT)
            + len(THESIS_HELDOUT)
            + len(ARGUMENT_HELDOUT)
            + len(EVIDENCE_HELDOUT)
            + len(CITATION_HELDOUT)
            + len(HALLUCINATION_CASES)
            + len(COACH_REFUSAL)
        ),
        "total_template": (
            len(question_gold())
            + len(thesis_gold())
            + len(citation_gold())
            + len(argument_gold())
            + len(evidence_gold())
            + len(rubric_gold())
        ),
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


def _metric(
    name: str,
    tp: int,
    fp: int,
    fn: int,
    support: int,
    confusion: dict | None = None,
    source: str = "circular",
    notes: str = "",
) -> Metric:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    p_ci = wilson_interval(tp, tp + fp)
    r_ci = wilson_interval(tp, tp + fn)
    if fp == fn and support > 0 and tp + fp == support:
        f_ci = wilson_interval(tp, support)
    else:
        f_ci = wilson_interval(round(f1 * support), support) if support else (0.0, 0.0)
    min_n = CERT_MIN_N.get(name, 1000)
    certifiable = (
        source == "heldout"
        and support >= min_n
        and p_ci[0] >= CERT_F1
        and r_ci[0] >= CERT_F1
        and f_ci[0] >= CERT_F1
    )
    if source == "circular":
        notes = notes or "Circular: labels generated from the same rules as the classifier. Not validity evidence."
    elif source == "heldout" and support < min_n:
        notes = notes or f"Independent held-out, but n={support} is below the {min_n} certification floor."
    return Metric(
        name,
        precision,
        recall,
        f1,
        tp,
        fp,
        fn,
        support,
        confusion or {},
        source,
        [round(p_ci[0], 4), round(p_ci[1], 4)],
        [round(r_ci[0], 4), round(r_ci[1], 4)],
        [round(f_ci[0], 4), round(f_ci[1], 4)],
        certifiable,
        notes,
    )

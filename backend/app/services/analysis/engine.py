from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from app.services.analysis.citations import CitationReport, analyze_citations
from app.services.analysis.question import QuestionAnalysis, analyze_question
from app.services.documents.extractor import ExtractedDocument

SEVERITIES = ("critical", "high", "medium", "low", "informational")
SCORE_CATEGORIES = (
    ("relevance", 18, "Assignment relevance"),
    ("thesis", 12, "Thesis"),
    ("argument", 14, "Argument"),
    ("evidence", 12, "Evidence"),
    ("structure", 12, "Structure"),
    ("academic_writing", 10, "Academic writing"),
    ("grammar", 10, "Grammar"),
    ("citations", 8, "Citations"),
    ("references", 4, "References"),
)

COMMAND_COVERAGE = {
    "compare": ["similar", "difference", "whereas", "however", "both", "unlike", "in contrast"],
    "evaluate": ["effective", "limited", "significant", "however", "therefore", "suggests", "implies"],
    "assess": ["effective", "limited", "significant", "impact"],
    "discuss": ["however", "although", "perspective", "argue", "view"],
    "analyse": ["because", "therefore", "this suggests", "implies", "relationship"],
    "analyze": ["because", "therefore", "this suggests", "implies"],
    "critically": ["limitation", "assumption", "however", "although", "not necessarily"],
}

THESIS_MARKERS = re.compile(
    r"\b(this (paper|essay|assignment|study|article)|i argue|this essay argues|"
    r"the (main )?argument|it (will be )?argued|this dissertation)\b",
    re.I,
)
CLAIM_MARKERS = re.compile(
    r"\b(therefore|thus|this shows|this suggests|it is clear|demonstrates|argues that|"
    r"this means|consequently|as a result)\b",
    re.I,
)
EVIDENCE_MARKERS = re.compile(
    r"\b(according to|research (shows|suggests|indicates)|a study|evidence|"
    r"statistics|percent|%|found that|reported that)\b",
    re.I,
)
HEDGES = re.compile(r"\b(may|might|suggests|appears|likely|possible|tends to|arguably)\b", re.I)
ABSOLUTES = re.compile(r"\b(always|never|everyone|no one|proves|undeniable|obviously|certainly)\b", re.I)
INFORMAL = re.compile(
    r"\b(a lot|really|very|stuff|things|kind of|sort of|gonna|wanna|awesome|nowadays)\b",
    re.I,
)
CONTRACTIONS = re.compile(r"\b\w+n't\b|\b(it's|that's|there's|they're|we're|you're|can't|won't|don't)\b", re.I)
FIRST_PERSON = re.compile(r"\b(i |me |my |we |our )\b", re.I)
TRANSITION = re.compile(
    r"^\s*(however|moreover|furthermore|in addition|therefore|consequently|in contrast|"
    r"on the other hand|nevertheless|similarly|for example|for instance)\b",
    re.I,
)


@dataclass
class Finding:
    category: str
    severity: str
    location: str
    paragraph: int | None
    original_text: str
    explanation: str
    suggestion: str
    teaching_note: str = ""
    example: str = ""
    improved_sentence: str = ""
    confidence: int = 70
    extra: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CategoryScore:
    category: str
    score: int
    max_score: int = 100
    weight: int = 10
    rationale: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalysisResult:
    question: QuestionAnalysis
    citation: CitationReport
    findings: list[Finding] = field(default_factory=list)
    scores: list[CategoryScore] = field(default_factory=list)
    overall_score: int = 0
    summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    priority_actions: list[str] = field(default_factory=list)
    other_improvements: list[str] = field(default_factory=list)
    structure_map: list[dict] = field(default_factory=list)
    readability: dict = field(default_factory=dict)
    word_count: dict = field(default_factory=dict)
    rubric: dict = field(default_factory=dict)
    thesis: dict = field(default_factory=dict)
    relevance: dict = field(default_factory=dict)
    ai_indicator: dict | None = None
    weakest_area: dict = field(default_factory=dict)
    score_breakdown: list[dict] = field(default_factory=list)
    disclaimer: str = (
        "AI-assisted analysis only. Results are not an official grade, "
        "plagiarism determination, or definitive AI-use determination."
    )

    def to_dict(self) -> dict:
        return {
            "question": self.question.to_dict(),
            "citation": self.citation.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "scores": [s.to_dict() for s in self.scores],
            "overall_score": self.overall_score,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "priority_actions": self.priority_actions,
            "other_improvements": self.other_improvements,
            "structure_map": self.structure_map,
            "readability": self.readability,
            "word_count": self.word_count,
            "rubric": self.rubric,
            "thesis": self.thesis,
            "relevance": self.relevance,
            "ai_indicator": self.ai_indicator,
            "weakest_area": self.weakest_area,
            "score_breakdown": self.score_breakdown,
            "disclaimer": self.disclaimer,
        }


def run_analysis(
    document: ExtractedDocument,
    question_text: str,
    academic_level: str = "undergraduate",
    citation_style: str = "apa7",
    rubric_criteria: list[dict] | None = None,
    include_ai_indicator: bool = False,
) -> AnalysisResult:
    question = analyze_question(question_text, academic_level)
    citation = analyze_citations(document.normalized_text, document.paragraphs, citation_style)
    body = [p for p in document.paragraphs if not p.is_heading]
    findings: list[Finding] = []

    relevance = _relevance(document, question)
    thesis = _thesis(document, question)
    structure_map, structure_findings = _structure(document)
    findings.extend(structure_findings)
    findings.extend(_introduction(document, thesis))
    findings.extend(_conclusion(document, question))
    findings.extend(_paragraphs(body, thesis.get("statement") or ""))
    findings.extend(_arguments(body))
    findings.extend(_evidence(body, citation))
    findings.extend(_coherence(body))
    findings.extend(_grammar(body))
    findings.extend(_academic_writing(body, academic_level))
    findings.extend(_citation_findings(citation))
    findings.extend(_relevance_findings(relevance))
    findings.extend(_thesis_findings(thesis))

    word_count = {
        "total": document.word_count,
        "excluding_references": document.word_count_excl_references,
        "excluding_headings": document.word_count_excl_headings,
        "paragraphs": document.paragraph_count,
        "sentences": document.sentence_count,
        "average_sentence_length": round(
            document.word_count / document.sentence_count, 1
        )
        if document.sentence_count
        else 0,
    }
    readability = _readability(document)

    scores = _scores(
        relevance=relevance,
        thesis=thesis,
        findings=findings,
        citation=citation,
        structure_map=structure_map,
        document=document,
    )
    overall, breakdown = _overall(scores)
    strengths, weaknesses, priority, other = _priorities(findings, scores)
    weakest = _weakest(scores, findings)
    rubric = _rubric(rubric_criteria, scores) if rubric_criteria else {}
    ai_indicator = _ai_indicator(document) if include_ai_indicator else None

    summary = (
        f"Diagnostic writing quality: {overall}/100. "
        f"This is an AI-assisted indicator, not an official academic grade. "
        f"{' '.join(priority[:2])}"
    )

    return AnalysisResult(
        question=question,
        citation=citation,
        findings=findings,
        scores=scores,
        overall_score=overall,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        priority_actions=priority,
        other_improvements=other,
        structure_map=structure_map,
        readability=readability,
        word_count=word_count,
        rubric=rubric,
        thesis=thesis,
        relevance=relevance,
        ai_indicator=ai_indicator,
        weakest_area=weakest,
        score_breakdown=breakdown,
    )


def _tokens(text: str) -> set[str]:
    stop = {
        "the", "and", "for", "that", "with", "this", "from", "your", "are", "was",
        "were", "have", "has", "had", "not", "but", "you", "their", "they", "them",
        "into", "onto", "about", "than", "then", "also", "such", "using", "use",
    }
    return {t for t in re.findall(r"[a-z]{3,}", text.lower()) if t not in stop}


def _relevance(document: ExtractedDocument, question: QuestionAnalysis) -> dict:
    q_tokens = _tokens(question.raw_text + " " + question.topic)
    d_tokens = _tokens(document.normalized_text[:12000])
    overlap = q_tokens & d_tokens if q_tokens else set()
    coverage_ratio = len(overlap) / max(len(q_tokens), 1)
    covered, weak, missing = [], [], []
    body = document.normalized_text.lower()
    for req in question.required:
        key = req.split("/")[0].strip().lower()
        cues = []
        for cmd, words in COMMAND_COVERAGE.items():
            if cmd in key or key in cmd:
                cues = words
        if not cues:
            cues = _tokens(req)
        hits = sum(1 for w in cues if w in body)
        if hits >= 2 or key in body:
            covered.append(req)
        elif hits == 1:
            weak.append(req)
        else:
            missing.append(req)
    if question.topic and any(t in body for t in _tokens(question.topic)):
        if "Topic alignment" not in covered:
            covered.append("Topic alignment")
    elif question.topic:
        missing.append("Clear focus on the assigned topic")

    score = int(min(100, max(20, coverage_ratio * 70 + len(covered) * 8 - len(missing) * 10)))
    return {
        "score": score,
        "covered": covered,
        "weakly_covered": weak,
        "missing": missing,
        "overlap_terms": sorted(list(overlap))[:20],
        "note": "This relevance score is a diagnostic reading of topic and requirement coverage, not a grade.",
    }


def _thesis(document: ExtractedDocument, question: QuestionAnalysis) -> dict:
    intro = document.paragraphs[: max(2, len(document.paragraphs) // 5)]
    candidates = []
    for p in intro:
        if p.is_heading:
            continue
        arguable = bool(
            THESIS_MARKERS.search(p.text)
            or re.search(r"\b(argue|argues|should|however|although|while|because)\b", p.text, re.I)
        )
        if arguable and len(p.text.split()) > 12 and "?" not in p.text:
            if _tokens(p.text) & (_tokens(question.topic) | _tokens(question.raw_text) | {"argue", "argues"}):
                candidates.append(p)
    statement = ""
    location = None
    if candidates:
        # Prefer the last substantial intro paragraph — common thesis placement.
        best = candidates[-1]
        statement = best.text
        location = best.index
    strength = "missing"
    reasons = []
    if not statement:
        reasons.append("No clear thesis statement was identified in the opening section.")
        strength = "missing"
    else:
        words = statement.split()
        q_overlap = _tokens(statement) & _tokens(question.raw_text)
        if len(words) < 12:
            strength = "weak"
            reasons.append("The possible thesis is too short to be a specific academic claim.")
        elif not q_overlap:
            strength = "weak"
            reasons.append("The possible thesis does not clearly answer the assignment question.")
        elif not any(w in statement.lower() for w in ("however", "because", "should", "argues", "argue", "while", "although")):
            strength = "moderate"
            reasons.append("A thesis-like sentence is present, but it may still be more descriptive than arguable.")
        else:
            strength = "strong"
            reasons.append("A specific, question-facing claim appears in the introduction.")
        if len(words) > 80:
            strength = "moderate" if strength == "strong" else strength
            reasons.append("The thesis may be too broad or contain too many claims at once.")
    return {
        "statement": statement,
        "strength": strength,
        "paragraph": location,
        "reasons": reasons,
    }


def _structure(document: ExtractedDocument) -> tuple[list[dict], list[Finding]]:
    findings: list[Finding] = []
    present = {s.section_type for s in document.sections}
    mapping = [
        ("introduction", "Introduction"),
        ("thesis", "Thesis"),
        ("body", "Argument / body"),
        ("counterargument", "Counterargument"),
        ("conclusion", "Conclusion"),
        ("references", "References"),
    ]
    thesis_present = any(THESIS_MARKERS.search(p.text) for p in document.paragraphs[:6])
    structure_map = []
    for key, label in mapping:
        if key == "thesis":
            status = "present" if thesis_present else "warning"
        elif key == "body":
            status = "present" if document.paragraph_count >= 3 else "warning"
        elif key in present:
            status = "present"
        elif key == "counterargument":
            has_counter = any(
                re.search(r"\b(however|critics|although|on the other hand|nevertheless)\b", p.text, re.I)
                for p in document.paragraphs
            )
            status = "present" if has_counter else "warning"
        else:
            status = "missing" if key in {"introduction", "conclusion"} else "warning"
        structure_map.append({"key": key, "label": label, "status": status})

    if all(s.section_type != "introduction" for s in document.sections) and document.paragraph_count > 0:
        findings.append(
            Finding(
                category="structure",
                severity="high",
                location="Opening",
                paragraph=0,
                original_text=document.paragraphs[0].text[:240] if document.paragraphs else "",
                explanation="The opening does not clearly establish context, focus, and a thesis.",
                suggestion="Rewrite the first paragraph so a reader can see the topic, the question, and your claim.",
                teaching_note="An introduction usually moves from context to focus to thesis.",
                confidence=68,
            )
        )
    if "conclusion" not in present and document.paragraph_count > 4:
        findings.append(
            Finding(
                category="structure",
                severity="high",
                location="Ending",
                paragraph=document.paragraphs[-1].index if document.paragraphs else None,
                original_text=document.paragraphs[-1].text[:240] if document.paragraphs else "",
                explanation="A distinct conclusion was not clearly detected.",
                suggestion="End by answering the question, synthesising the main arguments, and avoiding new major claims.",
                teaching_note="A conclusion should synthesise, not merely repeat the introduction.",
                confidence=64,
            )
        )
    if "counterargument" not in present:
        findings.append(
            Finding(
                category="argument",
                severity="medium",
                location="Argument as a whole",
                paragraph=None,
                original_text="",
                explanation="No clear counterargument section was detected. Evaluation is weaker if opposing views are ignored.",
                suggestion="Acknowledge at least one serious opposing view and explain why your position still holds.",
                teaching_note="Counterargument shows you can weigh evidence rather than only advocate.",
                confidence=60,
            )
        )
    return structure_map, findings


def _introduction(document: ExtractedDocument, thesis: dict) -> list[Finding]:
    findings = []
    if not document.paragraphs:
        return findings
    first = next((p for p in document.paragraphs if not p.is_heading), None)
    if not first:
        return findings
    text = first.text
    if re.match(r"^(since the dawn|throughout history|in today's society|dictionary|according to the oxford)", text, re.I):
        findings.append(
            Finding(
                category="introduction",
                severity="medium",
                location="Introduction",
                paragraph=first.index,
                original_text=text[:240],
                explanation="The opening uses a very broad or dictionary-style start that delays the assignment question.",
                suggestion="Open with the specific debate or problem the question raises.",
                example="Rather than 'Since the dawn of time...', name the phenomenon, place, and tension immediately.",
                confidence=78,
            )
        )
    if thesis.get("strength") == "missing":
        findings.append(
            Finding(
                category="introduction",
                severity="high",
                location="Introduction",
                paragraph=first.index,
                original_text=text[:240],
                explanation="The introduction does not appear to contain a thesis that answers the question.",
                suggestion="Add a specific, arguable sentence that states your answer before the first body paragraph.",
                teaching_note="A thesis is a contestable claim, not a topic announcement.",
                confidence=72,
            )
        )
    return findings


def _conclusion(document: ExtractedDocument, question: QuestionAnalysis) -> list[Finding]:
    if not document.paragraphs:
        return []
    last = document.paragraphs[-1]
    for p in reversed(document.paragraphs):
        if not p.is_heading and _tokens(p.text):
            last = p
            break
    findings = []
    overlap = _tokens(last.text) & _tokens(question.raw_text)
    if len(last.text.split()) < 40:
        findings.append(
            Finding(
                category="conclusion",
                severity="medium",
                location="Conclusion",
                paragraph=last.index,
                original_text=last.text[:240],
                explanation="The ending is brief and may not synthesise the argument or answer the question.",
                suggestion="Close by restating your judgement and showing how the main arguments support it.",
                confidence=66,
            )
        )
    if question.command_words and not overlap:
        findings.append(
            Finding(
                category="conclusion",
                severity="high",
                location="Conclusion",
                paragraph=last.index,
                original_text=last.text[:240],
                explanation="The ending does not clearly return to the wording of the assignment question.",
                suggestion="Make the final judgement answer the command words directly (for example, compare and evaluate).",
                confidence=63,
            )
        )
    if re.search(r"\b(a new|another important|future research should also consider an entirely)\b", last.text, re.I):
        findings.append(
            Finding(
                category="conclusion",
                severity="medium",
                location="Conclusion",
                paragraph=last.index,
                original_text=last.text[:240],
                explanation="The conclusion may be introducing a major new line of argument.",
                suggestion="Keep new material small — an implication is fine; a new case is usually not.",
                confidence=60,
            )
        )
    return findings


def _paragraphs(body: list, thesis: str) -> list[Finding]:
    findings = []
    seen_starts: list[str] = []
    for p in body:
        words = p.text.split()
        if p.is_heading or len(words) < 12:
            continue
        first_sentence = re.split(r"(?<=[.!?])\s+", p.text, maxsplit=1)[0]
        strength = "strong"
        issue = ""
        suggestion = ""
        if len(words) < 40:
            strength = "weak"
            issue = "The paragraph is too short to develop a claim, evidence, and explanation."
            suggestion = "Expand the paragraph so it contains a point, evidence, and an explanation of why the evidence matters."
        elif not EVIDENCE_MARKERS.search(p.text) and not re.search(r"\((?:[A-Z]|\[)", p.text):
            strength = "moderate"
            issue = "The paragraph states ideas but may not show evidence or citation."
            suggestion = "Add a source, example, or data point, then explain how it supports the claim."
        elif EVIDENCE_MARKERS.search(p.text) and not CLAIM_MARKERS.search(p.text) and "because" not in p.text.lower():
            strength = "moderate"
            issue = "Evidence is presented but its connection to the argument is not clearly explained."
            suggestion = "After the evidence, add a sentence that explains how it supports your claim."
        if thesis and not (_tokens(p.text) & _tokens(thesis)) and p.index > 1:
            if strength == "strong":
                strength = "moderate"
            if not issue:
                issue = "The paragraph may not clearly link back to the thesis."
                suggestion = "End the paragraph by showing how this point advances your overall answer."
        start_key = " ".join(first_sentence.lower().split()[:6])
        if start_key in seen_starts:
            findings.append(
                Finding(
                    category="paragraph",
                    severity="low",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=first_sentence[:240],
                    explanation="This paragraph appears to repeat an earlier opening idea.",
                    suggestion="Combine repeated points or give this paragraph a distinct role in the argument.",
                    confidence=58,
                )
            )
        seen_starts.append(start_key)
        if issue:
            findings.append(
                Finding(
                    category="paragraph",
                    severity="medium" if strength != "weak" else "high",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=p.text[:280],
                    explanation=f"Strength: {strength.capitalize()}. {issue}",
                    suggestion=suggestion,
                    teaching_note="A strong academic paragraph usually has a topic sentence, evidence, explanation, and a link to the thesis.",
                    extra={"strength": strength},
                    confidence=67,
                )
            )
    return findings


def _arguments(body: list) -> list[Finding]:
    findings = []
    claims = [p for p in body if CLAIM_MARKERS.search(p.text) or len(p.text.split()) > 60]
    if len(claims) < 2 and body:
        findings.append(
            Finding(
                category="argument",
                severity="high",
                location="Argument as a whole",
                paragraph=body[0].index,
                original_text=body[0].text[:240],
                explanation="Few distinct claims were detected. The work may be describing the topic rather than arguing a case.",
                suggestion="State 2–4 clear claims and develop each with evidence and analysis.",
                teaching_note="Description reports what is; argument explains significance and takes a position.",
                confidence=62,
            )
        )
    texts = [p.text.lower() for p in body]
    if any("beneficial" in t or "positive" in t for t in texts) and any("harmful" in t or "negative" in t for t in texts):
        # Contradiction is not automatically an error in comparison essays.
        pass
    unsupported = [
        p
        for p in body
        if re.search(r"\b(all|proves|never|always|the fact that)\b", p.text, re.I)
        and not EVIDENCE_MARKERS.search(p.text)
    ]
    for p in unsupported[:4]:
        findings.append(
            Finding(
                category="argument",
                severity="medium",
                location=f"Paragraph {p.index + 1}",
                paragraph=p.index,
                original_text=p.text[:240],
                explanation="This passage makes a strong assertion that may not be supported by evidence in the same paragraph.",
                suggestion="Soften the claim or add a source, then analyse it.",
                confidence=61,
            )
        )
    return findings


def _evidence(body: list, citation: CitationReport) -> list[Finding]:
    findings = []
    cited_paras = {c.paragraph_index for c in citation.citations}
    for p in body:
        needs = bool(
            re.search(
                r"\b(\d+%|\d{4}|study|research|gdp|inflation|unemployment|war|treaty|experiment)\b",
                p.text,
                re.I,
            )
        )
        if not needs:
            continue
        if p.index in cited_paras or EVIDENCE_MARKERS.search(p.text):
            classification = "supported" if p.index in cited_paras else "needs_citation"
        else:
            classification = "potentially_unsupported"
        if classification != "supported":
            findings.append(
                Finding(
                    category="evidence",
                    severity="high" if classification == "potentially_unsupported" else "medium",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=p.text[:240],
                    explanation=(
                        "This passage contains a claim that often requires a source. "
                        f"Classification: {classification.replace('_', ' ')}. "
                        "Absence of a citation does not mean the statement is false."
                    ),
                    suggestion="Add a citation if this is not common knowledge in your discipline, or explain why the claim is your analysis.",
                    extra={"classification": classification},
                    confidence=64,
                )
            )
    return findings


def _coherence(body: list) -> list[Finding]:
    findings = []
    prev_tokens: set[str] = set()
    abrupt = 0
    for p in body:
        tokens = _tokens(p.text)
        if prev_tokens and tokens and len(prev_tokens & tokens) < 2 and not TRANSITION.search(p.text):
            abrupt += 1
            if abrupt <= 3:
                findings.append(
                    Finding(
                        category="coherence",
                        severity="low",
                        location=f"Paragraph {p.index + 1}",
                        paragraph=p.index,
                        original_text=p.text[:180],
                        explanation="This paragraph may shift topic abruptly from the previous one.",
                        suggestion="Add a conceptual bridge — not just a transition word — that shows why this point follows.",
                        teaching_note="Coherence comes from related ideas, not from inserting 'Moreover' everywhere.",
                        confidence=55,
                    )
                )
        prev_tokens = tokens
    return findings


def _grammar(body: list) -> list[Finding]:
    findings = []
    rules = [
        (re.compile(r"\b(a)\s+([aeiou]\w+)", re.I), "Article usage", "Use 'an' before a vowel sound."),
        (re.compile(r"\b(their|there|they're)\b", re.I), "Possible homophone", "Check that their/there/they're is the intended word."),
        (re.compile(r"\b(its|it's)\b"), "Possible its/it's confusion", "Use its for possession and it's only for it is."),
        (re.compile(r"\s+,", re.I), "Punctuation", "Remove the space before the comma."),
        (re.compile(r"\b(is|are|was|were)\s+\w+ed\b"), "Possible passive construction", "Passive voice is acceptable in academic writing; use it when the actor is unknown or unimportant."),
    ]
    for p in body:
        if len(p.text.split()) > 55 and p.text.count(",") >= 4 and p.text.count(".") == 0:
            findings.append(
                Finding(
                    category="grammar",
                    severity="medium",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=p.text[:220],
                    explanation="This looks like a run-on or overly long sentence.",
                    suggestion="Split the sentence at a logical clause boundary.",
                    confidence=70,
                )
            )
        if re.search(r"\b(although|because|when|if|while)\b.+(,)?\s*$", p.text.strip(), re.I) and len(p.text.split()) < 18:
            findings.append(
                Finding(
                    category="grammar",
                    severity="medium",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=p.text[:220],
                    explanation="This may be a sentence fragment.",
                    suggestion="Attach the dependent clause to a complete main clause.",
                    confidence=63,
                )
            )
        for pattern, problem, suggestion in rules:
            m = pattern.search(p.text)
            if not m:
                continue
            findings.append(
                Finding(
                    category="grammar",
                    severity="low",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=m.group(0),
                    explanation=problem,
                    suggestion=suggestion,
                    improved_sentence="",
                    confidence=58,
                )
            )
            if len([f for f in findings if f.category == "grammar"]) > 12:
                return findings
    return findings


def _academic_writing(body: list, level: str) -> list[Finding]:
    findings = []
    for p in body:
        if INFORMAL.search(p.text) or CONTRACTIONS.search(p.text):
            findings.append(
                Finding(
                    category="academic_writing",
                    severity="low",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=p.text[:200],
                    explanation="The wording is more conversational than typical academic prose.",
                    suggestion="Replace informal phrases with precise terms. Prefer clarity over complicated vocabulary.",
                    confidence=74,
                )
            )
        if ABSOLUTES.search(p.text) and not HEDGES.search(p.text):
            findings.append(
                Finding(
                    category="academic_writing",
                    severity="medium",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=p.text[:200],
                    explanation="An absolute statement appears without hedging or evidence.",
                    suggestion="If the claim is not universally true, qualify it (for example, 'in many cases', 'the evidence suggests').",
                    teaching_note="Hedging is not weakness; it shows you understand the limits of evidence.",
                    confidence=66,
                )
            )
        if level in {"undergraduate", "masters", "phd"} and FIRST_PERSON.search(p.text) and "i argue" not in p.text.lower():
            findings.append(
                Finding(
                    category="academic_writing",
                    severity="informational",
                    location=f"Paragraph {p.index + 1}",
                    paragraph=p.index,
                    original_text=p.text[:180],
                    explanation="First person is used. This is acceptable in many disciplines, but some markers prefer a more impersonal voice.",
                    suggestion="Keep first person if you are stating your argument; avoid it for unsupported personal narrative.",
                    confidence=50,
                )
            )
    # Deduplicate similar low-severity hits
    unique = []
    seen = set()
    for f in findings:
        key = (f.category, f.paragraph, f.explanation[:40])
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)
    return unique[:15]


def _citation_findings(citation: CitationReport) -> list[Finding]:
    findings = []
    if citation.mismatches:
        findings.append(
            Finding(
                category="citations",
                severity="high",
                location="Citations and references",
                paragraph=None,
                original_text="; ".join(citation.mismatches[:3]),
                explanation=citation.summary,
                suggestion="Every in-text citation should correspond to a full reference, and every reference should be cited.",
                teaching_note="A mismatch is a formatting or completeness issue, not proof that a source is fabricated.",
                confidence=70,
            )
        )
    if citation.duplicates:
        findings.append(
            Finding(
                category="references",
                severity="low",
                location="Reference list",
                paragraph=None,
                original_text=citation.duplicates[0],
                explanation="Possible duplicate references were detected.",
                suggestion="Keep one complete reference entry and remove repeats.",
                confidence=72,
            )
        )
    missing_meta = [r for r in citation.references if r.missing_fields]
    if missing_meta:
        findings.append(
            Finding(
                category="references",
                severity="medium",
                location="Reference list",
                paragraph=None,
                original_text=missing_meta[0].raw_text[:220],
                explanation=f"{len(missing_meta)} reference(s) appear to be missing common fields such as author, date, or title.",
                suggestion="Complete the missing fields from the source itself. A DOI is useful but not required for every reference.",
                confidence=68,
            )
        )
    if not citation.citations and not citation.references:
        findings.append(
            Finding(
                category="citations",
                severity="high",
                location="Document",
                paragraph=None,
                original_text="",
                explanation="No in-text citations or reference list were clearly detected.",
                suggestion="If the assignment requires sources, add citations in the required style and a matching reference list.",
                confidence=75,
            )
        )
    return findings


def _relevance_findings(relevance: dict) -> list[Finding]:
    findings = []
    if relevance["missing"]:
        findings.append(
            Finding(
                category="relevance",
                severity="critical",
                location="Assignment question",
                paragraph=None,
                original_text=", ".join(relevance["missing"]),
                explanation="Some requirements suggested by the question wording appear missing or very weak.",
                suggestion="Address each missing requirement in a dedicated paragraph or section.",
                confidence=70,
            )
        )
    if relevance["weakly_covered"]:
        findings.append(
            Finding(
                category="relevance",
                severity="high",
                location="Assignment question",
                paragraph=None,
                original_text=", ".join(relevance["weakly_covered"]),
                explanation="These requirements appear only weakly developed.",
                suggestion="Add judgement, comparison, or analysis — not just extra description.",
                confidence=66,
            )
        )
    return findings


def _thesis_findings(thesis: dict) -> list[Finding]:
    if thesis["strength"] in {"strong"}:
        return []
    severity = "critical" if thesis["strength"] == "missing" else "high"
    return [
        Finding(
            category="thesis",
            severity=severity,
            location="Introduction",
            paragraph=thesis.get("paragraph"),
            original_text=(thesis.get("statement") or "")[:280],
            explanation=" ".join(thesis.get("reasons") or []),
            suggestion="Write one specific, arguable sentence that answers the question and can be supported by the rest of the essay.",
            teaching_note="A thesis is a claim a reasonable reader could disagree with, not a restatement of the topic.",
            example="Weak: 'This essay is about globalization.' Stronger: 'Globalization has expanded trade in developing economies, but the gains are uneven because bargaining power and industrial policy differ across states.'",
            confidence=73,
        )
    ]


def _readability(document: ExtractedDocument) -> dict:
    words = max(document.word_count, 1)
    sentences = max(document.sentence_count, 1)
    asl = words / sentences
    # Approximate syllables
    text = document.normalized_text[:20000]
    syllables = max(1, len(re.findall(r"[aeiouy]+", text.lower())))
    # Flesch-ish, explained as diagnostic only
    flesch = 206.835 - 1.015 * asl - 84.6 * (syllables / words)
    flesch = max(0, min(100, round(flesch, 1)))
    passive = len(re.findall(r"\b(?:is|are|was|were|be|been)\s+\w+ed\b", text, re.I))
    return {
        "score": flesch,
        "average_sentence_length": round(asl, 1),
        "average_paragraph_words": round(words / max(document.paragraph_count, 1), 1),
        "approx_passive_constructions": passive,
        "explanation": (
            "This readability score estimates how demanding the prose is. "
            "A lower score does not automatically mean better academic writing. "
            "University work can be complex when the ideas require it."
        ),
    }


def _clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def _scores(relevance, thesis, findings, citation, structure_map, document) -> list[CategoryScore]:
    by_cat: dict[str, list[Finding]] = {}
    for f in findings:
        by_cat.setdefault(f.category, []).append(f)

    def penalty(cats: tuple[str, ...], base: int) -> int:
        items = [f for c in cats for f in by_cat.get(c, [])]
        deduct = 0
        for f in items:
            deduct += {"critical": 14, "high": 8, "medium": 4, "low": 2, "informational": 0}.get(f.severity, 3)
        return _clamp(base - deduct)

    present = sum(1 for s in structure_map if s["status"] == "present")
    structure_score = _clamp(55 + present * 7)
    thesis_score = {"strong": 88, "moderate": 70, "weak": 48, "missing": 28}.get(thesis["strength"], 50)
    citation_score = 88
    if citation.mismatches:
        citation_score -= min(30, 8 * len(citation.mismatches))
    if not citation.citations:
        citation_score = 40 if document.word_count > 400 else 70
    reference_score = 85
    if citation.references:
        missing = sum(1 for r in citation.references if r.missing_fields)
        reference_score = _clamp(90 - missing * 6)
    elif citation.citations:
        reference_score = 42
    else:
        reference_score = 55

    mapping = {
        "relevance": (relevance["score"], "How far the work appears to address the question wording."),
        "thesis": (thesis_score, "Whether a specific, question-facing claim is present."),
        "argument": (penalty(("argument",), 80), "Claim development, counterargument, and reasoning."),
        "evidence": (penalty(("evidence",), 82), "Whether claims that typically need sources are supported."),
        "structure": (structure_score, "Presence and order of academic sections."),
        "academic_writing": (penalty(("academic_writing", "coherence"), 84), "Formality, precision, and cohesion."),
        "grammar": (penalty(("grammar",), 90), "Surface language issues detected by rules and patterns."),
        "citations": (_clamp(citation_score), "In-text citation presence and possible mismatches."),
        "references": (_clamp(reference_score), "Reference-list completeness and consistency."),
    }
    scores = []
    for key, weight, _label in SCORE_CATEGORIES:
        value, rationale = mapping[key]
        scores.append(CategoryScore(category=key, score=_clamp(value), weight=weight, rationale=rationale))
    return scores


def _overall(scores: list[CategoryScore]) -> tuple[int, list[dict]]:
    total_weight = sum(s.weight for s in scores) or 1
    weighted = sum(s.score * s.weight for s in scores) / total_weight
    overall = _clamp(round(weighted))
    breakdown = [
        {
            "category": s.category,
            "score": s.score,
            "weight": s.weight,
            "weighted_points": round(s.score * s.weight / total_weight, 2),
            "rationale": s.rationale,
        }
        for s in scores
    ]
    return overall, breakdown


def _priorities(findings: list[Finding], scores: list[CategoryScore]) -> tuple[list[str], list[str], list[str], list[str]]:
    ranked_scores = sorted(scores, key=lambda s: s.score)
    strengths = [s.category.replace("_", " ").title() for s in sorted(scores, key=lambda s: -s.score)[:3] if s.score >= 78]
    weaknesses = [s.category.replace("_", " ").title() for s in ranked_scores[:3] if s.score < 80]
    severe = [f for f in findings if f.severity in {"critical", "high"}]
    mild = [f for f in findings if f.severity in {"medium", "low"}]
    priority = []
    for f in severe:
        line = f.explanation.split(".")[0].strip()
        if line and line not in priority:
            priority.append(line + ".")
        if len(priority) >= 5:
            break
    other = []
    for f in mild:
        line = f.explanation.split(".")[0].strip()
        if line and line not in other and line + "." not in priority:
            other.append(line + ".")
        if len(other) >= 8:
            break
    return strengths, weaknesses, priority, other


def _weakest(scores: list[CategoryScore], findings: list[Finding]) -> dict:
    weakest = min(scores, key=lambda s: s.score)
    related = next((f for f in findings if f.category == weakest.category), None)
    return {
        "category": weakest.category,
        "score": weakest.score,
        "label": weakest.category.replace("_", " ").title(),
        "explanation": related.explanation if related else weakest.rationale,
        "why_it_matters": (
            "Markers often weight this area heavily because it affects whether the work answers the question "
            "and can be assessed as academic argument rather than summary."
        ),
        "how_to_improve": related.suggestion if related else "Revise this area first, then re-check the draft.",
        "example": related.example if related else "",
        "finding": related.to_dict() if related else None,
    }


def _rubric(criteria: list[dict], scores: list[CategoryScore]) -> dict:
    score_map = {s.category: s.score for s in scores}
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
    }
    rows = []
    estimated = 0
    weight_sum = 0
    for item in criteria:
        name = str(item.get("name") or "Criterion")
        weight = int(item.get("weight_percent") or item.get("max_points") or 0)
        max_points = int(item.get("max_points") or weight or 10)
        key = "academic_writing"
        lowered = name.lower()
        for alias, mapped in aliases.items():
            if alias in lowered:
                key = mapped
                break
        awarded = round((score_map.get(key, 70) / 100) * max_points)
        rows.append({"name": name, "awarded": awarded, "max_points": max_points, "weight_percent": weight})
        estimated += awarded
        weight_sum += max_points
    total = int(round((estimated / weight_sum) * 100)) if weight_sum else 0
    return {
        "criteria": rows,
        "estimated_total": total,
        "label": "AI-assisted rubric assessment — not an official grade.",
        "disclaimer": "This does not claim to know a lecturer's actual grade.",
    }


def _ai_indicator(document: ExtractedDocument) -> dict:
    text = document.normalized_text
    sentences = re.split(r"(?<=[.!?])\s+", text)
    lengths = [len(s.split()) for s in sentences if s.split()]
    if not lengths:
        return {"level": "low", "explanation": "Not enough text to assess stylistic uniformity.", "signals": []}
    mean = sum(lengths) / len(lengths)
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    std = math.sqrt(variance)
    generic = len(re.findall(r"\b(in conclusion|it is important to note|in today's society|moreover|furthermore)\b", text, re.I))
    signals = []
    level = "low"
    if std < 4 and len(lengths) > 12:
        signals.append("Sentence length is unusually uniform.")
        level = "moderate"
    if generic >= 6:
        signals.append("Repeated formulaic academic transitions appear frequently.")
        level = "moderate"
    if std < 3 and generic >= 8:
        level = "high"
        signals.append("Organization and phrasing look highly formulaic.")
    if not signals:
        signals.append("No strong uniformity or formulaic-pattern signals were detected.")
    return {
        "level": level,
        "signals": signals,
        "explanation": (
            "This is a qualitative stylistic indicator, not proof of AI use. "
            "Human writers can be formulaic, and AI-assisted writing can be revised into a personal voice. "
            "Do not treat this as a misconduct finding."
        ),
        "disclaimer": "Never interpret this indicator as 'this student definitely used AI'.",
    }

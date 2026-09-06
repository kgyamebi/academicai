from app.services.ai.eval import load_baseline, run_all, suite_sizes, thesis_gold, write_baseline
from app.services.analysis.classifiers import classify_thesis
from app.services.analysis.engine import run_analysis
from app.services.documents.extractor import ExtractedDocument, ExtractedParagraph


def test_evaluation_suite_has_10000_cases():
    sizes = suite_sizes()
    assert sizes["total"] >= 10000
    assert sizes["question"] >= 1000
    assert sizes["thesis"] >= 1000
    assert sizes["argument"] >= 1000
    assert sizes["evidence"] >= 1000
    assert sizes["rubric"] >= 50
    assert sizes["citation"] >= 20


def test_ai_quality_does_not_regress():
    metrics = run_all()
    baseline = load_baseline()
    if not baseline:
        write_baseline(metrics)
        baseline = load_baseline()
    by_name = {m.name: m for m in metrics}
    for name, previous in baseline.items():
        current = by_name[name].f1
        assert current + 0.03 >= previous, f"{name} F1 dropped from {previous} to {current}"
    assert by_name["question_analyzer"].f1 >= 0.90
    assert by_name["citation_extractor"].f1 >= 0.90
    assert by_name["thesis_analyzer"].f1 >= 0.95
    assert by_name["argument_analyzer"].f1 >= 0.95
    assert by_name["evidence_analyzer"].f1 >= 0.95
    assert by_name["rubric_checker"].f1 >= 0.95
    write_baseline(metrics)


def test_engine_thesis_matches_classifier_on_gold_sample():
    for question, draft, expected in thesis_gold()[:24]:
        predicted = classify_thesis(draft, question)
        assert predicted == expected
        result = run_analysis(_doc(draft), question)
        assert result.thesis.get("strength") == expected


def _doc(text: str) -> ExtractedDocument:
    para = ExtractedParagraph(
        index=0,
        text=text,
        is_heading=False,
        heading_level=0,
        char_start=0,
        char_end=len(text),
        word_count=len(text.split()),
    )
    words = len(text.split())
    return ExtractedDocument(
        text=text,
        normalized_text=text,
        paragraphs=[para],
        sections=[],
        word_count=words,
        word_count_excl_references=words,
        word_count_excl_headings=words,
        paragraph_count=1,
        sentence_count=max(1, text.count(".") + text.count("?")),
        page_count=1,
        language="en",
    )

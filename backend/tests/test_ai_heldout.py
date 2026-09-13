from app.services.ai.hallucination import allow_model_text
from app.services.ai.heldout import HALLUCINATION_CASES, QUESTION_HELDOUT, THESIS_HELDOUT
from app.services.analysis.classifiers import classify_evidence, classify_thesis
from app.services.analysis.question import analyze_question


def test_heldout_command_words():
    for text, expected in QUESTION_HELDOUT:
        found = {w.lower() for w in analyze_question(text).command_words}
        assert expected <= found, (text, expected, found)


def test_heldout_thesis_labels():
    for question, draft, expected in THESIS_HELDOUT:
        assert classify_thesis(draft, question) == expected


def test_evidence_four_way_labels():
    assert classify_evidence("GDP grew by 7 percent after reform.") == "needs_citation"
    assert classify_evidence("GDP grew by 7 percent after reform (Rodrik, 2011).") == "supported"
    assert classify_evidence("A thesis should be contestable.") == "cannot_determine"
    assert classify_evidence("Everyone knows that globalization always proves that poverty disappears.") == (
        "potentially_unsupported"
    )


def test_hallucination_cases():
    for output, allowed, should_pass in HALLUCINATION_CASES:
        assert allow_model_text(output, allowed) is should_pass

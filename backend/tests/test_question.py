from app.services.analysis.question import analyze_question


def test_compare_and_evaluate_question():
    result = analyze_question(
        "Compare and evaluate the effects of globalization on developing economies.",
        "undergraduate",
    )
    assert "compare and evaluate" in result.command_words
    assert "Comparison" in result.required
    assert any("Evaluation" in item for item in result.required)
    assert "developing economies" in result.geographic_scope
    assert "lecturer wants" not in result.interpretation.lower()
    assert "based on the wording" in result.interpretation.lower()

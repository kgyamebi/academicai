from app.services.analysis.engine import run_analysis
from app.services.documents.extractor import extract_document

QUESTION = "Compare and evaluate the effects of globalization on developing economies."

ESSAY = """
Introduction

Globalization has changed trade, labour and policy in many developing economies. This essay argues that globalization has expanded market access, but the gains are uneven because bargaining power and industrial policy differ across states.

Trade and growth

Trade openness is associated with faster export growth in several developing economies (Rodrik, 2011). This suggests that access to markets can raise output, but it does not prove that every country benefits equally.

Labour and inequality

However, wage gains are often concentrated in urban export sectors. Critics argue that rural households may see weaker gains. The comparison therefore matters more than a single national average.

Evaluation

Overall, globalization appears beneficial where states can bargain and upgrade industry, and more limited where policy capacity is weak. This evaluation is tentative because country cases differ.

Conclusion

Based on the comparison above, globalization should not be judged as uniformly good or bad for developing economies. The effects depend on policy and power.

References

Rodrik, D. (2011). The globalization paradox. W. W. Norton.
"""


def test_full_analysis_produces_transparent_score():
    extracted = extract_document(ESSAY.encode(), ".txt")
    result = run_analysis(extracted, QUESTION, "undergraduate", "apa7")
    assert 40 <= result.overall_score <= 95
    cats = {s.category for s in result.scores}
    assert {"relevance", "thesis", "argument", "evidence", "structure", "grammar", "citations"}.issubset(cats)
    assert result.disclaimer.startswith("AI-assisted")
    assert result.word_count["total"] > 50
    assert result.question.command_words
    assert result.weakest_area["category"]
    assert result.structure_map


def test_missing_thesis_is_flagged():
    text = "Globalization is a topic. Many people talk about it. Things happen in the world. " * 20
    extracted = extract_document(text.encode(), ".txt")
    result = run_analysis(extracted, QUESTION, "undergraduate", "apa7")
    assert result.thesis["strength"] in {"missing", "weak"}
    assert any(f.category == "thesis" for f in result.findings)


def test_citation_mismatch_detected():
    text = """
    Globalization raised GDP growth (Smith, 2019). Other work disagrees (Jones, 2020).

    References
    Smith, A. (2019). Trade and growth. Journal of Example Studies.
    """
    extracted = extract_document(text.encode(), ".txt")
    result = run_analysis(extracted, QUESTION, "undergraduate", "apa7")
    assert result.citation.citations
    assert result.citation.mismatches or "Jones" in " ".join(result.citation.mismatches)

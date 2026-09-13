from types import SimpleNamespace

from app.services.reports import build_pdf_report


def _report():
    score = SimpleNamespace(category="thesis", score=72, max_score=100, rationale="A contestable claim appears.")
    finding = SimpleNamespace(
        category="thesis",
        severity="medium",
        explanation="The thesis could be more specific.",
        suggestion="Name the claim in one sentence.",
    )
    return SimpleNamespace(
        overall_score=68,
        summary="The draft addresses the question with mixed evaluation.",
        strengths_json='["Clear comparison"]',
        weaknesses_json='["Thin evaluation"]',
        priority_actions_json='["Strengthen the thesis"]',
        scores=[score],
        findings=[finding],
        rubric_json="{}",
        disclaimer="Diagnostic only. Not an official grade.",
    )


def test_pdf_has_title_language_and_extractable_text():
    pdf = build_pdf_report(_report(), "Globalization assignment")
    assert pdf.startswith(b"%PDF")
    assert b"/Title" in pdf
    assert b"/Lang" in pdf or b"en-GB" in pdf
    assert b"AcademicCheck AI" in pdf

    import fitz

    doc = fitz.open(stream=pdf, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    meta = doc.metadata or {}
    doc.close()
    assert "AcademicCheck AI" in text
    assert "Globalization assignment" in text
    assert "Overall diagnostic score" in text
    assert "Category scores" in text
    assert "Thesis" in text or "thesis" in text.lower()
    assert meta.get("title")
    assert "AcademicCheck" in (meta.get("title") or "")


def test_pdf_is_searchable_and_not_image_only():
    pdf = build_pdf_report(_report(), "Searchable draft")
    import fitz

    doc = fitz.open(stream=pdf, filetype="pdf")
    words = []
    for page in doc:
        words.extend(page.get_text("words"))
    doc.close()
    assert len(words) > 20

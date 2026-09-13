from __future__ import annotations

import io
import json
from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.crypto import decrypt_field
from app.models.analysis import AnalysisReport

TEAL = colors.Color(0.06, 0.46, 0.43)
INK = colors.Color(0.04, 0.07, 0.13)
MUTED = colors.Color(0.36, 0.42, 0.48)
RULE = colors.Color(0.89, 0.91, 0.94)
SOFT = colors.Color(0.93, 0.97, 0.96)


def _health_label(score: int) -> str:
    if score >= 85:
        return "Very Strong Draft"
    if score >= 75:
        return "Strong Draft"
    if score >= 60:
        return "Solid Foundation"
    if score >= 45:
        return "Developing Draft"
    return "Needs Focused Revision"


def build_pdf_report(report: AnalysisReport, assignment_title: str) -> bytes:
    buffer = io.BytesIO()
    title = f"AcademicCheck AI — {assignment_title}"
    doc_kwargs = dict(
        pagesize=A4,
        title=title,
        author="AcademicCheck AI",
        subject="Assignment analysis report",
        creator="AcademicCheck AI",
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )
    try:
        doc = SimpleDocTemplate(buffer, lang="en-GB", **doc_kwargs)
    except TypeError:
        doc = SimpleDocTemplate(buffer, **doc_kwargs)

    styles = getSampleStyleSheet()
    brand = ParagraphStyle("Brand", parent=styles["Normal"], fontName="Times-Bold", fontSize=11, textColor=TEAL, spaceAfter=4)
    h1 = ParagraphStyle("H1AC", parent=styles["Heading1"], fontName="Times-Bold", fontSize=20, textColor=INK, spaceAfter=8)
    h2 = ParagraphStyle("H2AC", parent=styles["Heading2"], fontName="Times-Bold", fontSize=13, textColor=INK, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("BodyAC", parent=styles["BodyText"], fontName="Times-Roman", fontSize=10, leading=14, textColor=INK)
    muted = ParagraphStyle("MutedAC", parent=styles["Normal"], fontName="Times-Roman", fontSize=9, leading=12, textColor=MUTED)
    italic = ParagraphStyle("ItalicAC", parent=styles["Italic"], fontName="Times-Italic", fontSize=9, leading=12, textColor=MUTED)

    overall = int(report.overall_score or 0)
    gaps = sorted((100 - int(s.score) for s in report.scores), reverse=True) if report.scores else []
    potential = int(round(sum(gaps[:3]) * 0.28)) if gaps else 0
    potential = max(0, min(22, potential))
    minutes = 5 if potential <= 6 else 12 if potential <= 12 else 20 if potential <= 16 else 35

    story = []
    story.append(Paragraph("AcademicCheck AI", brand))
    story.append(Paragraph("Assignment analysis report", h1))
    story.append(Paragraph(_esc(assignment_title), body))
    story.append(Paragraph(datetime.now(UTC).strftime("%d %B %Y"), muted))
    story.append(Spacer(1, 0.12 * inch))
    story.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceAfter=10))

    story.append(Paragraph(f"Overall diagnostic score: {overall}/100", h2))
    story.append(Paragraph(f"<b>{_esc(_health_label(overall))}</b> · Improvement potential +{potential} · ~{minutes} minutes", body))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(_esc(decrypt_field(report.summary)), body))
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Category scores", h2))
    score_rows = [["Category", "Score", "Rationale"]]
    for score in report.scores:
        score_rows.append(
            [
                score.category.replace("_", " ").title(),
                f"{score.score}/{score.max_score}",
                Paragraph(_esc(score.rationale), muted),
            ]
        )
    story.append(
        Table(
            score_rows,
            colWidths=[1.5 * inch, 0.85 * inch, 4.15 * inch],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), SOFT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), TEAL),
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    story.append(Paragraph("Fix-First — priority actions", h2))
    for i, item in enumerate(_loads(report.priority_actions_json)[:5], start=1):
        story.append(Paragraph(f"<b>{i:02d}.</b> {_esc(str(item))}", body))

    story.append(Paragraph("Strengths", h2))
    for item in _loads(report.strengths_json):
        story.append(Paragraph(f"• {_esc(str(item))}", body))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph("Highest-priority weaknesses", h2))
    for item in _loads(report.weaknesses_json):
        story.append(Paragraph(f"• {_esc(str(item))}", body))

    story.append(Paragraph("Detailed findings", h2))
    for finding in report.findings[:40]:
        story.append(
            Paragraph(
                f"<b>{_esc(finding.category.title())} — {finding.severity}</b>: {_esc(decrypt_field(finding.explanation))}",
                body,
            )
        )
        if finding.suggestion:
            story.append(Paragraph(f"Suggestion: {_esc(decrypt_field(finding.suggestion))}", muted))

    rubric = _loads(report.rubric_json)
    if rubric:
        story.append(Paragraph("Rubric analysis", h2))
        story.append(Paragraph(_esc(str(rubric.get("label", ""))), body))
        for row in rubric.get("criteria") or []:
            story.append(
                Paragraph(
                    f"{_esc(row.get('name', ''))}: {row.get('awarded')} / {row.get('max_points')}",
                    body,
                )
            )

    story.append(Spacer(1, 0.25 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=8))
    story.append(Paragraph(_esc(report.disclaimer), italic))
    story.append(
        Paragraph(
            "Always follow your institution’s academic-integrity policies. "
            "Citation verification may not find every legitimate source. "
            "AI-writing indicators are not proof of AI use.",
            italic,
        )
    )
    doc.build(story, onFirstPage=_stamp_pdf_ua, onLaterPages=_stamp_pdf_ua)
    return _ensure_pdf_ua(buffer.getvalue(), title)


def _stamp_pdf_ua(canvas, doc) -> None:
    canvas.setTitle(doc.title or "AcademicCheck AI report")
    canvas.setAuthor("AcademicCheck AI")
    canvas.setSubject("Assignment analysis report")
    canvas.setCreator("AcademicCheck AI")
    if hasattr(canvas, "setLanguage"):
        canvas.setLanguage("en-GB")


def _ensure_pdf_ua(payload: bytes, title: str) -> bytes:
    """Guarantee catalog language and marked-content flag even if ReportLab omits them."""
    if b"/Lang" in payload and b"/MarkInfo" in payload and b"/Title" in payload:
        return payload
    try:
        import fitz

        doc = fitz.open(stream=payload, filetype="pdf")
        doc.set_metadata(
            {
                "title": title,
                "author": "AcademicCheck AI",
                "subject": "Assignment analysis report",
                "creator": "AcademicCheck AI",
                "producer": "AcademicCheck AI",
            }
        )
        try:
            doc.set_language("en-GB")
        except Exception as exc:  # noqa: BLE001
            from app.core.logging import get_logger

            get_logger("reports").debug("pdf_set_language_unsupported", error=str(exc))
        out = doc.tobytes()
        doc.close()
        if b"/Lang" not in out:
            out = out.replace(b"/Type /Catalog", b"/Type /Catalog /Lang (en-GB) /MarkInfo << /Marked true >>", 1)
        elif b"/MarkInfo" not in out:
            out = out.replace(b"/Lang", b"/MarkInfo << /Marked true >> /Lang", 1)
        return out
    except Exception:  # noqa: BLE001
        patched = payload
        if b"/Lang" not in patched:
            patched = patched.replace(b"/Type /Catalog", b"/Type /Catalog /Lang (en-GB)", 1)
        if b"/MarkInfo" not in patched:
            patched = patched.replace(b"/Type /Catalog", b"/Type /Catalog /MarkInfo << /Marked true >>", 1)
        return patched


def _loads(raw: str):
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

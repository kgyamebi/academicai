from __future__ import annotations

import io
import json
from datetime import UTC, datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.core.crypto import decrypt_field
from app.models.analysis import AnalysisReport


def build_pdf_report(report: AnalysisReport, assignment_title: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"AcademicCheck AI — {assignment_title}")
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("AcademicCheck AI", styles["Title"]))
    story.append(Paragraph("Assignment analysis report", styles["Heading2"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(_esc(assignment_title), styles["Heading3"]))
    story.append(Paragraph(datetime.now(UTC).strftime("%d %B %Y"), styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Overall diagnostic score: {report.overall_score}/100", styles["Heading2"]))
    story.append(Paragraph(_esc(decrypt_field(report.summary)), styles["BodyText"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Category scores", styles["Heading2"]))
    for score in report.scores:
        story.append(
            Paragraph(
                f"{score.category.replace('_', ' ').title()}: {score.score}/{score.max_score} — {_esc(score.rationale)}",
                styles["BodyText"],
            )
        )
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Strengths", styles["Heading2"]))
    for item in _loads(report.strengths_json):
        story.append(Paragraph(f"• {_esc(str(item))}", styles["BodyText"]))
    story.append(Paragraph("Highest-priority weaknesses", styles["Heading2"]))
    for item in _loads(report.weaknesses_json):
        story.append(Paragraph(f"• {_esc(str(item))}", styles["BodyText"]))
    story.append(Paragraph("Priority actions", styles["Heading2"]))
    for item in _loads(report.priority_actions_json):
        story.append(Paragraph(f"• {_esc(str(item))}", styles["BodyText"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Detailed findings", styles["Heading2"]))
    for finding in report.findings[:40]:
        story.append(
            Paragraph(
                f"<b>{_esc(finding.category.title())} — {finding.severity}</b>: {_esc(decrypt_field(finding.explanation))}",
                styles["BodyText"],
            )
        )
        if finding.suggestion:
            story.append(Paragraph(f"Suggestion: {_esc(decrypt_field(finding.suggestion))}", styles["BodyText"]))
    rubric = _loads(report.rubric_json)
    if rubric:
        story.append(Paragraph("Rubric analysis", styles["Heading2"]))
        story.append(Paragraph(_esc(str(rubric.get("label", ""))), styles["BodyText"]))
        for row in rubric.get("criteria") or []:
            story.append(
                Paragraph(
                    f"{_esc(row.get('name', ''))}: {row.get('awarded')} / {row.get('max_points')}",
                    styles["BodyText"],
                )
            )
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(_esc(report.disclaimer), styles["Italic"]))
    story.append(
        Paragraph(
            "Always follow your institution’s academic-integrity policies. "
            "Citation verification may not find every legitimate source. "
            "AI-writing indicators are not proof of AI use.",
            styles["Italic"],
        )
    )
    doc.build(story)
    return buffer.getvalue()


def _loads(raw: str):
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []


def _esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

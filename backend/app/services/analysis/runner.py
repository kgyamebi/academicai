from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.analysis import AIIndicatorReport, AnalysisFinding, AnalysisJob, AnalysisReport, AnalysisScore
from app.models.assignment import Assignment
from app.models.citation import Citation, Reference
from app.models.document import Document, DocumentParagraph, DocumentSection
from app.services.ai.enhance import enhance_analysis
from app.services.ai.provider import PROMPT_VERSION
from app.services.analysis.engine import AnalysisResult, run_analysis
from app.services.documents.extractor import ExtractedDocument, ExtractedParagraph, ExtractedSection

log = get_logger("analysis.runner")

STAGES = (
    "queued",
    "extracting",
    "analyzing_structure",
    "checking_arguments",
    "checking_citations",
    "generating_report",
    "completed",
)


def process_job(db: Session, job_id: UUID) -> None:
    job = db.get(AnalysisJob, job_id)
    if not job or job.status in {"cancelled", "completed"}:
        return
    started = datetime.now(UTC)
    job.status = "processing"
    job.stage = "extracting"
    job.started_at = started
    db.commit()
    try:
        document = db.get(Document, job.document_id) if job.document_id else None
        assignment = db.get(Assignment, job.assignment_id) if job.assignment_id else None
        if not document:
            raise RuntimeError("Document not found for analysis job.")
        extracted = _document_to_extracted(db, document)
        job.stage = "analyzing_structure"
        db.commit()
        question_text = assignment.question.raw_text if assignment and assignment.question else ""
        rubric_criteria = []
        if assignment and assignment.rubric:
            rubric_criteria = [
                {"name": c.name, "weight_percent": c.weight_percent, "max_points": c.max_points}
                for c in assignment.rubric.criteria
            ]
        include_ai = job.analysis_type in {"full", "pro"}
        result = run_analysis(
            extracted,
            question_text,
            academic_level=assignment.academic_level if assignment else "undergraduate",
            citation_style=assignment.citation_style if assignment else "apa7",
            rubric_criteria=rubric_criteria or None,
            include_ai_indicator=include_ai,
        )
        job.stage = "checking_arguments"
        db.commit()
        job.stage = "checking_citations"
        db.commit()
        tokens = 0
        prompt_version = PROMPT_VERSION
        if job.analysis_type in {"full", "academic", "pro"}:
            job.stage = "generating_report"
            db.commit()
            result, tokens, prompt_version = enhance_analysis(result, extracted.normalized_text)
        _persist_citations(db, document, result)
        report = _persist_report(db, job, result)
        job.status = "completed"
        job.stage = "completed"
        job.completed_at = datetime.now(UTC)
        job.token_usage = tokens
        job.prompt_version = prompt_version
        job.model = "heuristic+optional-llm"
        job.duration_ms = int((job.completed_at - started).total_seconds() * 1000)
        job.estimated_cost_usd = Decimal(tokens) * Decimal("0.000002")
        db.commit()
        log.info("analysis_completed", job_id=str(job.id), report_id=str(report.id), score=result.overall_score)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job:
            job.status = "failed"
            job.error = "We couldn’t analyze this document. Please try again or upload a different file."
            job.completed_at = datetime.now(UTC)
            db.commit()
        log.error("analysis_failed", job_id=str(job_id), error=str(exc))


def _document_to_extracted(db: Session, document: Document) -> ExtractedDocument:
    paragraphs = db.query(DocumentParagraph).filter(DocumentParagraph.document_id == document.id).order_by(
        DocumentParagraph.index
    ).all()
    sections = db.query(DocumentSection).filter(DocumentSection.document_id == document.id).order_by(
        DocumentSection.sort_order
    ).all()
    return ExtractedDocument(
        text=document.extracted_text,
        normalized_text=document.normalized_text or document.extracted_text,
        paragraphs=[
            ExtractedParagraph(
                index=p.index,
                text=p.text,
                is_heading=p.is_heading,
                heading_level=p.heading_level,
                char_start=p.char_start,
                char_end=p.char_end,
                word_count=p.word_count,
            )
            for p in paragraphs
        ],
        sections=[
            ExtractedSection(
                heading=s.heading,
                section_type=s.section_type,
                start_paragraph=s.start_paragraph,
                end_paragraph=s.end_paragraph,
                sort_order=s.sort_order,
            )
            for s in sections
        ],
        word_count=document.word_count,
        word_count_excl_references=document.word_count_excl_references,
        word_count_excl_headings=document.word_count_excl_headings,
        paragraph_count=document.paragraph_count,
        sentence_count=document.sentence_count,
        page_count=document.page_count,
        language=document.language,
    )


def _persist_citations(db: Session, document: Document, result: AnalysisResult) -> None:
    db.query(Citation).filter(Citation.document_id == document.id).delete()
    db.query(Reference).filter(Reference.document_id == document.id).delete()
    for c in result.citation.citations:
        db.add(
            Citation(
                document_id=document.id,
                raw_text=c.raw_text,
                style_guess=c.style_guess,
                author=c.author,
                year=c.year,
                locator=c.locator,
                paragraph_index=c.paragraph_index,
                char_start=c.char_start,
                char_end=c.char_end,
            )
        )
    for r in result.citation.references:
        db.add(
            Reference(
                document_id=document.id,
                raw_text=r.raw_text,
                author=r.author,
                year=r.year,
                title=r.title,
                journal=r.journal,
                publisher=r.publisher,
                doi=r.doi,
                url=r.url,
                missing_fields=", ".join(r.missing_fields),
                sort_order=r.sort_order,
            )
        )


def _persist_report(db: Session, job: AnalysisJob, result: AnalysisResult) -> AnalysisReport:
    report = AnalysisReport(
        job_id=job.id,
        assignment_id=job.assignment_id,
        document_id=job.document_id,
        user_id=job.user_id,
        overall_score=result.overall_score,
        summary=result.summary,
        strengths_json=json.dumps(result.strengths),
        weaknesses_json=json.dumps(result.weaknesses),
        priority_actions_json=json.dumps(result.priority_actions),
        structure_map_json=json.dumps(result.structure_map),
        question_analysis_json=json.dumps(result.question.to_dict()),
        readability_json=json.dumps(result.readability),
        word_count_json=json.dumps(result.word_count),
        rubric_json=json.dumps(result.rubric),
        disclaimer=result.disclaimer,
    )
    db.add(report)
    db.flush()
    for f in result.findings:
        db.add(
            AnalysisFinding(
                report_id=report.id,
                category=f.category,
                severity=f.severity,
                location=f.location,
                paragraph=f.paragraph,
                original_text=f.original_text,
                explanation=f.explanation,
                suggestion=f.suggestion,
                teaching_note=f.teaching_note,
                example=f.example,
                improved_sentence=f.improved_sentence,
                confidence=f.confidence,
                extra=f.extra,
            )
        )
    for s in result.scores:
        db.add(
            AnalysisScore(
                report_id=report.id,
                category=s.category,
                score=s.score,
                max_score=s.max_score,
                weight=s.weight,
                rationale=s.rationale,
            )
        )
    if result.ai_indicator:
        db.add(
            AIIndicatorReport(
                report_id=report.id,
                level=result.ai_indicator.get("level", "low"),
                explanation=result.ai_indicator.get("explanation", ""),
                signals_json=json.dumps(result.ai_indicator.get("signals") or []),
                disclaimer=result.ai_indicator.get("disclaimer", ""),
            )
        )
    db.flush()
    return report

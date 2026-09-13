from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_field, encrypt_field
from app.core.logging import get_logger
from app.core.metrics import incr
from app.core.time import utcnow
from app.config import get_settings
from app.models.analysis import AIIndicatorReport, AnalysisFinding, AnalysisJob, AnalysisReport, AnalysisScore
from app.models.assignment import Assignment
from app.models.citation import Citation, Reference
from app.models.document import Document, DocumentParagraph, DocumentSection
from app.services.ai.enhance import enhance_analysis
from app.services.ai.provider import PROMPT_VERSION
from app.services.analysis.engine import AnalysisResult, run_analysis
from app.services.documents.extractor import ExtractedDocument, ExtractedParagraph, ExtractedSection

log = get_logger("analysis.runner")

STALE_JOB_SECONDS = 900
ORPHAN_HEARTBEAT_SECONDS = 90
MAX_JOB_RECOVERIES = 1

STAGES = (
    "queued",
    "extracting",
    "analyzing_structure",
    "checking_arguments",
    "checking_citations",
    "generating_report",
    "completed",
)


def touch_job_heartbeat(db: Session, job: AnalysisJob, *, stage: str | None = None) -> None:
    job.heartbeat_at = utcnow()
    if stage:
        job.stage = stage
    db.flush()


def recover_orphaned_jobs(db: Session, *, older_than_seconds: int = ORPHAN_HEARTBEAT_SECONDS) -> list[UUID]:
    """Reset killed mid-flight jobs to queued exactly once for safe re-queue."""
    cutoff = utcnow() - timedelta(seconds=older_than_seconds)
    orphans = list(
        db.scalars(
            select(AnalysisJob).where(
                AnalysisJob.status == "processing",
                or_(
                    (AnalysisJob.heartbeat_at.is_not(None)) & (AnalysisJob.heartbeat_at < cutoff),
                    (AnalysisJob.heartbeat_at.is_(None))
                    & (AnalysisJob.started_at.is_not(None))
                    & (AnalysisJob.started_at < cutoff),
                ),
            )
        )
    )
    recovered: list[UUID] = []
    for job in orphans:
        if (job.recovery_count or 0) >= MAX_JOB_RECOVERIES:
            fail_job(db, job.id, "Analysis worker crashed; job could not be recovered safely.")
            continue
        job.status = "queued"
        job.stage = "queued"
        job.error = None
        job.started_at = None
        job.heartbeat_at = None
        job.recovery_count = (job.recovery_count or 0) + 1
        recovered.append(job.id)
        incr("jobs.recovered")
        log.warning("analysis_job_recovered", job_id=str(job.id), recovery_count=job.recovery_count)
    if orphans:
        db.flush()
    return recovered


def fail_job(db: Session, job_id: UUID, error: str) -> bool:
    job = db.get(AnalysisJob, job_id)
    if not job or job.status in {"completed", "cancelled", "failed"}:
        return False
    from app.services.credits import refund_reservation

    job.status = "failed"
    job.error = error
    job.completed_at = utcnow()
    refund_reservation(db, job.id)
    incr("jobs.failed")
    return True


def reap_stale_jobs(db: Session, older_than_seconds: int = STALE_JOB_SECONDS) -> int:
    recover_orphaned_jobs(db)
    cutoff = utcnow() - timedelta(seconds=older_than_seconds)
    stale = list(
        db.scalars(
            select(AnalysisJob).where(
                or_(
                    (AnalysisJob.status == "processing") & (AnalysisJob.started_at < cutoff),
                    (AnalysisJob.status == "queued") & (AnalysisJob.created_at < cutoff),
                )
            )
        )
    )
    marked = 0
    for job in stale:
        if fail_job(db, job.id, "Analysis timed out. Please try again."):
            marked += 1
    if marked:
        db.flush()
    purge_expired_guest_documents(db)
    return marked


def purge_expired_guest_documents(db: Session) -> int:
    """Soft-delete guest documents past expires_at and remove stored bytes."""
    from app.services.documents.storage import delete_bytes

    now = utcnow()
    expired = list(
        db.scalars(
            select(Document).where(
                Document.expires_at.is_not(None),
                Document.expires_at < now,
                Document.deleted_at.is_(None),
            )
        )
    )
    n = 0
    for document in expired:
        document.deleted_at = now
        document.extracted_text = ""
        document.normalized_text = ""
        try:
            delete_bytes(document.storage_key)
        except Exception as exc:  # noqa: BLE001
            log.error("guest_purge_storage_failed", error=str(exc))
        n += 1
    if n:
        db.flush()
        log.info("guest_documents_purged", count=n)
    return n


def process_job(db: Session, job_id: UUID) -> None:
    reap_stale_jobs(db)
    job = db.get(AnalysisJob, job_id)
    if not job or job.status in {"cancelled", "completed", "failed"}:
        return
    started = utcnow()
    job.status = "processing"
    job.stage = "extracting"
    job.started_at = started
    job.heartbeat_at = started
    db.commit()
    incr("jobs.started")
    try:
        document = db.get(Document, job.document_id) if job.document_id else None
        assignment = db.get(Assignment, job.assignment_id) if job.assignment_id else None
        if not document:
            raise RuntimeError("Document not found for analysis job.")
        extracted = _document_to_extracted(db, document)
        touch_job_heartbeat(db, job, stage="analyzing_structure")
        db.commit()
        question_text = decrypt_field(assignment.question.raw_text) if assignment and assignment.question else ""
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
        touch_job_heartbeat(db, job, stage="checking_arguments")
        db.commit()
        touch_job_heartbeat(db, job, stage="checking_citations")
        db.commit()
        tokens = 0
        prompt_version = PROMPT_VERSION
        if job.analysis_type in {"full", "academic", "pro"}:
            touch_job_heartbeat(db, job, stage="generating_report")
            db.commit()
            result, tokens, prompt_version = enhance_analysis(result, extracted.normalized_text)
        db.expire(job)
        job = db.get(AnalysisJob, job_id)
        if not job or job.status in {"cancelled", "failed"}:
            return
        _persist_citations(db, document, result)
        report = _persist_report(db, job, result)
        from app.models.user import User
        from app.services.credits import consume_reservation
        from app.services.entitlements import increment_usage

        db.expire(job)
        job = db.get(AnalysisJob, job_id)
        if not job or job.status in {"cancelled", "failed"}:
            return
        job.status = "completed"
        job.stage = "completed"
        job.completed_at = utcnow()
        job.token_usage = tokens
        job.prompt_version = prompt_version
        job.model = "heuristic+optional-llm"
        job.duration_ms = int((job.completed_at - started).total_seconds() * 1000)
        job.estimated_cost_usd = Decimal(tokens) * Decimal("0.000002")
        consume_reservation(db, job.id)
        owner = db.get(User, job.user_id)
        if owner:
            increment_usage(db, owner)
            if not owner.is_guest and owner.email:
                from app.services.email_templates import analysis_ready_email
                from app.services.emailer import send_email

                settings = get_settings()
                report_url = f"{settings.app_web_url.rstrip('/')}/app/reports/{report.id}"
                subject, html, text = analysis_ready_email(
                    name=owner.full_name or "there",
                    score=result.overall_score,
                    report_url=report_url,
                )
                send_email(owner.email, subject, text, html=html)
        db.commit()
        incr("jobs.completed")
        log.info("analysis_completed", job_id=str(job.id), report_id=str(report.id), score=result.overall_score)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        if fail_job(db, job_id, "We couldn’t analyze this document. Please try again or upload a different file."):
            db.commit()
        log.error("analysis_failed", job_id=str(job_id), error=str(exc), exc_info=exc)
        from app.core.alerting import notify_worker_failure

        notify_worker_failure(job_id=str(job_id), error=str(exc), stage="process_job")


def _document_to_extracted(db: Session, document: Document) -> ExtractedDocument:
    paragraphs = db.query(DocumentParagraph).filter(DocumentParagraph.document_id == document.id).order_by(
        DocumentParagraph.index
    ).all()
    sections = db.query(DocumentSection).filter(DocumentSection.document_id == document.id).order_by(
        DocumentSection.sort_order
    ).all()
    return ExtractedDocument(
        text=decrypt_field(document.extracted_text),
        normalized_text=decrypt_field(document.normalized_text or document.extracted_text),
        paragraphs=[
            ExtractedParagraph(
                index=p.index,
                text=decrypt_field(p.text),
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
    existing = db.scalar(select(AnalysisReport).where(AnalysisReport.job_id == job.id))
    if existing:
        return existing
    report = AnalysisReport(
        job_id=job.id,
        assignment_id=job.assignment_id,
        document_id=job.document_id,
        user_id=job.user_id,
        overall_score=result.overall_score,
        summary=encrypt_field(result.summary),
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
    db.add_all(
        [
            AnalysisFinding(
                report_id=report.id,
                category=f.category,
                severity=f.severity,
                location=f.location,
                paragraph=f.paragraph,
                original_text=encrypt_field(f.original_text),
                explanation=encrypt_field(f.explanation),
                suggestion=encrypt_field(f.suggestion),
                teaching_note=encrypt_field(f.teaching_note),
                example=encrypt_field(f.example),
                improved_sentence=encrypt_field(f.improved_sentence),
                confidence=f.confidence,
                extra=f.extra,
            )
            for f in result.findings
        ]
    )
    db.add_all(
        [
            AnalysisScore(
                report_id=report.id,
                category=s.category,
                score=s.score,
                max_score=s.max_score,
                weight=s.weight,
                rationale=s.rationale,
            )
            for s in result.scores
        ]
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

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.rate_limit import check_rate_limit
from app.core.time import utcnow
from app.db.session import get_db
from app.deps import get_current_user, owned_assignment, owned_document
from app.models.analysis import AnalysisJob, AnalysisReport, ComparisonReport
from app.models.assignment import AssignmentVersion
from app.models.document import Document
from app.models.user import User
from app.schemas.common import AnalysisCreateIn, CompareIn
from app.services.analysis.runner import process_job, reap_stale_jobs
from app.services.credits import refund_reservation, reserve_credits
from app.services.entitlements import assert_can_analyze, monthly_quota_exhausted
from app.workers.queue import enqueue_analysis

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("")
def create_analysis(
    payload: AnalysisCreateIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "analysis", user)
    assignment = owned_assignment(payload.assignment_id, user, db)
    document = None
    if payload.document_id:
        document = owned_document(payload.document_id, user, db)
    else:
        document = (
            db.query(Document)
            .filter(Document.assignment_id == assignment.id, Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
            .first()
        )
    if not document:
        raise HTTPException(400, "Upload or paste a document before starting analysis.")
    if document.assignment_id and document.assignment_id != assignment.id:
        raise HTTPException(404, "Document not found.")
    if document.status in {"queued", "extracting"}:
        raise HTTPException(409, "Document is still being processed. Poll GET /api/documents/{id} until status is extracted.")
    if document.status != "extracted":
        raise HTTPException(400, document.extraction_error or "This document could not be read. Upload a different file.")
    assert_can_analyze(db, user, document.word_count, payload.analysis_type)
    spend_credits = monthly_quota_exhausted(db, user)
    job = AnalysisJob(
        user_id=user.id,
        assignment_id=assignment.id,
        document_id=document.id,
        status="queued",
        stage="queued",
        analysis_type=payload.analysis_type,
    )
    db.add(job)
    db.flush()
    if spend_credits:
        reserve_credits(db, user, payload.analysis_type, job.id)
    db.commit()
    db.refresh(job)
    queued = enqueue_analysis(str(job.id))
    settings = get_settings()
    if not queued:
        if settings.is_production or settings.require_queue:
            job.status = "failed"
            job.error = "Analysis workers are unavailable. Please try again shortly."
            refund_reservation(db, job.id)
            db.commit()
            raise HTTPException(503, "Analysis workers are unavailable. Please try again shortly.")
        process_job(db, job.id)
        db.refresh(job)
    return {"id": str(job.id), "status": job.status, "stage": job.stage}


@router.get("/{job_id}")
def get_analysis(job_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reap_stale_jobs(db)
    db.commit()
    job = db.get(AnalysisJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Analysis not found.")
    return {
        "id": str(job.id),
        "status": job.status,
        "stage": job.stage,
        "error": job.error,
        "report_id": str(job.report.id) if job.report else None,
    }


@router.post("/{job_id}/cancel")
def cancel_analysis(job_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(AnalysisJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Analysis not found.")
    if job.status in {"completed", "failed"}:
        return {"id": str(job.id), "status": job.status}
    job.status = "cancelled"
    job.cancelled_at = utcnow()
    refund_reservation(db, job.id)
    db.commit()
    return {"id": str(job.id), "status": job.status}


@router.post("/compare")
def compare(payload: CompareIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.auth import assert_email_verified

    assert_email_verified(user)
    assignment = owned_assignment(payload.assignment_id, user, db)
    version_a = db.get(AssignmentVersion, payload.version_a_id)
    version_b = db.get(AssignmentVersion, payload.version_b_id)
    if (
        not version_a
        or not version_b
        or version_a.assignment_id != assignment.id
        or version_b.assignment_id != assignment.id
    ):
        raise HTTPException(404, "Version not found.")
    report_a = _report_for_version(db, user.id, assignment.id, version_a.document_id)
    report_b = _report_for_version(db, user.id, assignment.id, version_b.document_id)
    if not report_a or not report_b:
        raise HTTPException(400, "Analyse both selected drafts before comparing versions.")
    scores_a = {s.category: s.score for s in report_a.scores}
    scores_b = {s.category: s.score for s in report_b.scores}
    improved = [k for k in scores_b if scores_b[k] > scores_a.get(k, 0) + 2]
    needs = [k for k in scores_b if scores_b[k] + 2 < scores_a.get(k, 0) or scores_b[k] < 70]
    summary = {
        "draft_1": report_a.overall_score,
        "draft_2": report_b.overall_score,
        "improved": [i.replace("_", " ").title() for i in improved],
        "needs_attention": [i.replace("_", " ").title() for i in needs[:5]],
        "categories": {k: {"draft_1": scores_a.get(k), "draft_2": scores_b.get(k)} for k in scores_b},
    }
    row = ComparisonReport(
        assignment_id=assignment.id,
        user_id=user.id,
        version_a_id=payload.version_a_id,
        version_b_id=payload.version_b_id,
        report_a_id=report_a.id,
        report_b_id=report_b.id,
        summary_json=json.dumps(summary),
    )
    db.add(row)
    db.commit()
    return summary


def _report_for_version(db: Session, user_id, assignment_id, document_id) -> AnalysisReport | None:
    if not document_id:
        return None
    return (
        db.query(AnalysisReport)
        .filter(
            AnalysisReport.assignment_id == assignment_id,
            AnalysisReport.user_id == user_id,
            AnalysisReport.document_id == document_id,
        )
        .order_by(AnalysisReport.created_at.desc())
        .first()
    )

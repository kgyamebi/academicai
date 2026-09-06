from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.deps import get_current_user, owned_assignment, owned_document
from app.models.analysis import AnalysisJob, AnalysisReport, ComparisonReport
from app.models.document import Document
from app.models.user import User
from app.schemas.common import AnalysisCreateIn, CompareIn
from app.services.entitlements import assert_can_analyze, increment_usage
from app.services.analysis.runner import process_job
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
    assert_can_analyze(db, user, document.word_count, payload.analysis_type)
    job = AnalysisJob(
        user_id=user.id,
        assignment_id=assignment.id,
        document_id=document.id,
        status="queued",
        stage="queued",
        analysis_type=payload.analysis_type,
    )
    db.add(job)
    increment_usage(db, user)
    db.commit()
    db.refresh(job)
    queued = enqueue_analysis(str(job.id))
    if not queued:
        process_job(db, job.id)
        db.refresh(job)
    return {"id": str(job.id), "status": job.status, "stage": job.stage}


@router.get("/{job_id}")
def get_analysis(job_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(AnalysisJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Analysis not found.")
    data = {
        "id": str(job.id),
        "status": job.status,
        "stage": job.stage,
        "error": job.error,
        "report_id": str(job.report.id) if job.report else None,
    }
    return data


@router.post("/{job_id}/cancel")
def cancel_analysis(job_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import UTC, datetime

    job = db.get(AnalysisJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Analysis not found.")
    if job.status in {"completed", "failed"}:
        return {"id": str(job.id), "status": job.status}
    job.status = "cancelled"
    job.cancelled_at = datetime.now(UTC)
    db.commit()
    return {"id": str(job.id), "status": job.status}


@router.post("/compare")
def compare(payload: CompareIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assignment = owned_assignment(payload.assignment_id, user, db)
    reports = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.assignment_id == assignment.id, AnalysisReport.user_id == user.id)
        .order_by(AnalysisReport.created_at.asc())
        .all()
    )
    if len(reports) < 2:
        raise HTTPException(400, "Analyse at least two drafts before comparing versions.")
    a = reports[0]
    b = reports[-1]
    scores_a = {s.category: s.score for s in a.scores}
    scores_b = {s.category: s.score for s in b.scores}
    improved = [k for k in scores_b if scores_b[k] > scores_a.get(k, 0) + 2]
    needs = [k for k in scores_b if scores_b[k] + 2 < scores_a.get(k, 0) or scores_b[k] < 70]
    summary = {
        "draft_1": a.overall_score,
        "draft_2": b.overall_score,
        "improved": [i.replace("_", " ").title() for i in improved],
        "needs_attention": [i.replace("_", " ").title() for i in needs[:5]],
        "categories": {k: {"draft_1": scores_a.get(k), "draft_2": scores_b.get(k)} for k in scores_b},
    }
    row = ComparisonReport(
        assignment_id=assignment.id,
        user_id=user.id,
        version_a_id=payload.version_a_id,
        version_b_id=payload.version_b_id,
        report_a_id=a.id,
        report_b_id=b.id,
        summary_json=json.dumps(summary),
    )
    db.add(row)
    db.commit()
    return summary

from __future__ import annotations

import json
import secrets
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.crypto import decrypt_field
from app.core.security import hash_password, hash_token, verify_password
from app.core.time import is_past, utcnow
from app.db.session import get_db
from app.deps import get_current_user
from app.models.admin import ShareAccessLog
from app.models.analysis import AnalysisFinding, AnalysisReport
from app.models.assignment import Assignment
from app.models.user import User
from app.schemas.common import ShareCreateIn, ShareUnlockIn
from app.services.reports import build_pdf_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _serialize_report(
    db: Session,
    report: AnalysisReport,
    include_findings: bool = True,
    page: int = 1,
    page_size: int = 40,
) -> dict:
    total = db.scalar(select(func.count(AnalysisFinding.id)).where(AnalysisFinding.report_id == report.id)) or 0
    findings: list[AnalysisFinding] = []
    if include_findings:
        findings = list(
            db.scalars(
                select(AnalysisFinding)
                .where(AnalysisFinding.report_id == report.id)
                .order_by(AnalysisFinding.created_at.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
    scores = report.scores
    weakest = min(scores, key=lambda s: s.score) if scores else None
    related = None
    if weakest:
        related = db.scalar(
            select(AnalysisFinding)
            .where(AnalysisFinding.report_id == report.id, AnalysisFinding.category == weakest.category)
            .order_by(AnalysisFinding.created_at.asc())
        )
    return {
        "id": str(report.id),
        "assignment_id": str(report.assignment_id) if report.assignment_id else None,
        "overall_score": report.overall_score,
        "summary": decrypt_field(report.summary),
        "disclaimer": report.disclaimer,
        "strengths": json.loads(report.strengths_json or "[]"),
        "weaknesses": json.loads(report.weaknesses_json or "[]"),
        "priority_actions": json.loads(report.priority_actions_json or "[]"),
        "structure_map": json.loads(report.structure_map_json or "[]"),
        "question": json.loads(report.question_analysis_json or "{}"),
        "readability": json.loads(report.readability_json or "{}"),
        "word_count": json.loads(report.word_count_json or "{}"),
        "rubric": json.loads(report.rubric_json or "{}"),
        "scores": [
            {"category": s.category, "score": s.score, "weight": s.weight, "rationale": s.rationale} for s in scores
        ],
        "findings": [_finding(f) for f in findings],
        "findings_total": total,
        "page": page,
        "page_size": page_size,
        "weakest_area": {
            "category": weakest.category if weakest else None,
            "score": weakest.score if weakest else None,
            "explanation": decrypt_field(related.explanation) if related else "",
            "how_to_improve": decrypt_field(related.suggestion) if related else "",
            "example": decrypt_field(related.example) if related else "",
            "teaching_note": decrypt_field(related.teaching_note) if related else "",
        }
        if weakest
        else {},
        "share_enabled": bool(report.share_token_hash and not report.share_revoked_at and not is_past(report.share_expires_at)),
        "share_protected": bool(report.share_password_hash),
        "share_expires_at": report.share_expires_at.isoformat() if report.share_expires_at else None,
    }


def _finding(f: AnalysisFinding) -> dict:
    return {
        "id": str(f.id),
        "category": f.category,
        "severity": f.severity,
        "location": f.location,
        "paragraph": f.paragraph,
        "original_text": decrypt_field(f.original_text),
        "explanation": decrypt_field(f.explanation),
        "suggestion": decrypt_field(f.suggestion),
        "teaching_note": decrypt_field(f.teaching_note),
        "example": decrypt_field(f.example),
        "improved_sentence": decrypt_field(f.improved_sentence),
    }


@router.get("/shared/{token}")
def public_share(token: str, request: Request, db: Session = Depends(get_db)):
    report = _shared_report(db, token)
    if report.share_password_hash:
        _audit(db, report, request, "view", False)
        db.commit()
        raise HTTPException(401, "This shared report is password protected.")
    _audit(db, report, request, "view", True)
    report.share_view_count = (report.share_view_count or 0) + 1
    db.commit()
    return _serialize_report(db, report, page_size=80)


@router.post("/shared/{token}")
def unlock_share(token: str, payload: ShareUnlockIn, request: Request, db: Session = Depends(get_db)):
    report = _shared_report(db, token)
    if report.share_password_hash and not (
        payload.password and verify_password(payload.password, report.share_password_hash)
    ):
        _audit(db, report, request, "unlock", False)
        db.commit()
        raise HTTPException(401, "Incorrect share password.")
    _audit(db, report, request, "unlock", True)
    report.share_view_count = (report.share_view_count or 0) + 1
    db.commit()
    return _serialize_report(db, report, page_size=80)


@router.get("/{report_id}")
def get_report(
    report_id: UUID,
    page: int = 1,
    page_size: int = 40,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.get(AnalysisReport, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(404, "Report not found.")
    return _serialize_report(db, report, page=page, page_size=page_size)


@router.get("/{report_id}/pdf")
def download_pdf(report_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.get(AnalysisReport, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(404, "Report not found.")
    assignment = db.get(Assignment, report.assignment_id) if report.assignment_id else None
    pdf = build_pdf_report(report, assignment.title if assignment else "Assignment")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=academiccheck-report.pdf"},
    )


@router.post("/{report_id}/share")
def create_share(
    report_id: UUID,
    payload: ShareCreateIn | None = Body(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.get(AnalysisReport, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(404, "Report not found.")
    token = secrets.token_urlsafe(24)
    hours = payload.hours if payload and payload.hours else get_settings().share_default_hours
    report.share_token_hash = hash_token(token)
    report.share_revoked_at = None
    report.share_expires_at = utcnow() + timedelta(hours=hours)
    report.share_view_count = 0
    report.share_password_hash = hash_password(payload.password) if payload and payload.password else None
    db.commit()
    return {
        "token": token,
        "path": f"/shared/{token}",
        "expires_at": report.share_expires_at.isoformat(),
        "password_protected": bool(report.share_password_hash),
    }


@router.post("/{report_id}/share/revoke")
def revoke_share(report_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.get(AnalysisReport, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(404, "Report not found.")
    report.share_revoked_at = utcnow()
    db.commit()
    return {"ok": True}


def _shared_report(db: Session, token: str) -> AnalysisReport:
    report = db.scalar(select(AnalysisReport).where(AnalysisReport.share_token_hash == hash_token(token)))
    if not report or report.share_revoked_at or is_past(report.share_expires_at):
        raise HTTPException(404, "This share link is unavailable.")
    return report


def _audit(db: Session, report: AnalysisReport, request: Request, action: str, success: bool) -> None:
    db.add(
        ShareAccessLog(
            report_id=report.id,
            action=action,
            success=success,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )

from __future__ import annotations

import secrets
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.core.crypto import decrypt_field
from app.core.pagination import decode_cursor, enforce_shallow_offset, keyset_after, next_cursor_from
from app.core.rate_limit import check_rate_limit
from app.core.security import hash_password, hash_token, verify_password
from app.core.time import is_past, utcnow
from app.db.session import get_db
from app.deps import get_current_user
from app.models.admin import ShareAccessLog
from app.models.analysis import AnalysisFinding, AnalysisReport
from app.models.assignment import Assignment
from app.models.user import User
from app.schemas.common import ShareCreateIn, ShareUnlockIn
from app.core.safe_json import loads_json
from app.services.reports import build_pdf_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _serialize_report(
    db: Session,
    report: AnalysisReport,
    include_findings: bool = True,
    page: int = 1,
    page_size: int = 40,
    cursor: str | None = None,
) -> dict:
    total = db.scalar(select(func.count(AnalysisFinding.id)).where(AnalysisFinding.report_id == report.id)) or 0
    findings: list[AnalysisFinding] = []
    if include_findings:
        filters = [AnalysisFinding.report_id == report.id]
        if cursor:
            ts, row_id = decode_cursor(cursor)
            filters.append(keyset_after(AnalysisFinding.created_at, AnalysisFinding.id, ts, row_id))
        else:
            enforce_shallow_offset(page, page_size)
        stmt = (
            select(AnalysisFinding)
            .where(*filters)
            .order_by(AnalysisFinding.created_at.asc(), AnalysisFinding.id.asc())
            .limit(page_size)
        )
        if not cursor:
            stmt = stmt.offset((page - 1) * page_size)
        findings = list(db.scalars(stmt))
    scores = report.scores
    weakest = min(scores, key=lambda s: s.score) if scores else None
    related = None
    if weakest:
        related = db.scalar(
            select(AnalysisFinding)
            .where(AnalysisFinding.report_id == report.id, AnalysisFinding.category == weakest.category)
            .order_by(AnalysisFinding.created_at.asc())
        )

    # Progress vs previous analysis on the same assignment (additive)
    previous = None
    previous_scores: list[dict] = []
    if report.assignment_id:
        previous = db.scalar(
            select(AnalysisReport)
            .options(selectinload(AnalysisReport.scores))
            .where(
                AnalysisReport.assignment_id == report.assignment_id,
                AnalysisReport.user_id == report.user_id,
                AnalysisReport.created_at < report.created_at,
            )
            .order_by(AnalysisReport.created_at.desc())
            .limit(1)
        )
        if previous:
            previous_scores = [
                {"category": s.category, "score": s.score} for s in (previous.scores or [])
            ]

    overall = int(report.overall_score or 0)
    health_level, health_label = _health_level(overall)
    gaps = sorted((100 - int(s.score) for s in scores), reverse=True) if scores else []
    improvement_potential = int(round(sum(gaps[:3]) * 0.28)) if gaps else 0
    improvement_potential = max(0, min(22, improvement_potential))
    est_minutes = 5 if improvement_potential <= 6 else 12 if improvement_potential <= 12 else 20 if improvement_potential <= 16 else 35
    confidence = (
        "High" if len(scores) >= 6 and total >= 1 else "Moderate" if len(scores) >= 4 else "Limited"
    )
    improvement_pct = None
    if previous and previous.overall_score is not None and previous.overall_score > 0:
        improvement_pct = int(round(((overall - previous.overall_score) / previous.overall_score) * 100))
    elif previous and previous.overall_score is not None:
        improvement_pct = overall - previous.overall_score

    category_changes = []
    if previous_scores:
        prev_map = {s["category"]: s["score"] for s in previous_scores}
        for s in scores:
            if s.category in prev_map:
                category_changes.append(
                    {
                        "category": s.category,
                        "previous": prev_map[s.category],
                        "current": s.score,
                        "delta": int(s.score - prev_map[s.category]),
                    }
                )

    return {
        "id": str(report.id),
        "assignment_id": str(report.assignment_id) if report.assignment_id else None,
        "overall_score": report.overall_score,
        "summary": decrypt_field(report.summary),
        "disclaimer": report.disclaimer,
        "strengths": loads_json(report.strengths_json, []),
        "weaknesses": loads_json(report.weaknesses_json, []),
        "priority_actions": loads_json(report.priority_actions_json, []),
        "structure_map": loads_json(report.structure_map_json, []),
        "question": loads_json(report.question_analysis_json, {}),
        "readability": loads_json(report.readability_json, {}),
        "word_count": loads_json(report.word_count_json, {}),
        "rubric": loads_json(report.rubric_json, {}),
        "scores": [
            {"category": s.category, "score": s.score, "weight": s.weight, "rationale": s.rationale} for s in scores
        ],
        "findings": [_finding(f) for f in findings],
        "findings_total": total,
        "page": page,
        "page_size": page_size,
        "next_cursor": next_cursor_from(findings, page_size=page_size, ts_attr="created_at")
        if include_findings
        else None,
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
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "health": {
            "level": health_level,
            "label": health_label,
            "confidence": confidence,
            "improvement_potential": improvement_potential,
            "estimated_minutes": est_minutes,
        },
        "progress": {
            "previous_score": previous.overall_score if previous else None,
            "current_score": overall,
            "improvement_pct": improvement_pct,
            "category_changes": category_changes,
            "previous_report_id": str(previous.id) if previous else None,
        },
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


def _health_level(score: int) -> tuple[str, str]:
    if score >= 85:
        return "exceptional", "Very Strong Draft"
    if score >= 75:
        return "strong", "Strong Draft"
    if score >= 60:
        return "solid", "Solid Foundation"
    if score >= 45:
        return "developing", "Developing Draft"
    return "focused", "Needs Focused Revision"


def _owned_report(db: Session, report_id: UUID, user_id: UUID, *options) -> AnalysisReport:
    stmt = select(AnalysisReport).where(AnalysisReport.id == report_id, AnalysisReport.user_id == user_id)
    if options:
        stmt = stmt.options(*options)
    report = db.scalar(stmt)
    if not report:
        raise HTTPException(404, "Report not found.")
    return report


@router.get("/shared/{token}")
def public_share(token: str, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "share")
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
    check_rate_limit(request, "share")
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
    page: int = Query(1, ge=1),
    page_size: int = Query(40, ge=1, le=100),
    cursor: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _owned_report(db, report_id, user.id, selectinload(AnalysisReport.scores))
    return _serialize_report(db, report, page=page, page_size=page_size, cursor=cursor)


@router.get("/{report_id}/pdf")
def download_pdf(report_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.auth import assert_email_verified

    assert_email_verified(user)
    report = _owned_report(db, report_id, user.id, selectinload(AnalysisReport.scores))
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
    from app.services.auth import assert_email_verified

    assert_email_verified(user)
    report = _owned_report(db, report_id, user.id)
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
    report = _owned_report(db, report_id, user.id)
    report.share_revoked_at = utcnow()
    db.commit()
    return {"ok": True}


def _shared_report(db: Session, token: str) -> AnalysisReport:
    report = db.scalar(
        select(AnalysisReport)
        .options(selectinload(AnalysisReport.scores))
        .where(AnalysisReport.share_token_hash == hash_token(token))
    )
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

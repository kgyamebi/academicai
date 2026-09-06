from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.db.session import get_db
from app.deps import get_current_user
from app.models.analysis import AnalysisFinding, AnalysisReport
from app.models.assignment import Assignment
from app.models.user import User
from app.services.reports import build_pdf_report
import secrets

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _serialize_report(report: AnalysisReport, include_findings: bool = True, page: int = 1, page_size: int = 40) -> dict:
    findings = report.findings
    start = (page - 1) * page_size
    chunk = findings[start : start + page_size] if include_findings else []
    weakest = min(report.scores, key=lambda s: s.score) if report.scores else None
    related = next((f for f in findings if weakest and f.category == weakest.category), None)
    return {
        "id": str(report.id),
        "assignment_id": str(report.assignment_id) if report.assignment_id else None,
        "overall_score": report.overall_score,
        "summary": report.summary,
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
            {"category": s.category, "score": s.score, "weight": s.weight, "rationale": s.rationale}
            for s in report.scores
        ],
        "findings": [_finding(f) for f in chunk],
        "findings_total": len(findings),
        "page": page,
        "page_size": page_size,
        "weakest_area": {
            "category": weakest.category if weakest else None,
            "score": weakest.score if weakest else None,
            "explanation": related.explanation if related else "",
            "how_to_improve": related.suggestion if related else "",
            "example": related.example if related else "",
            "teaching_note": related.teaching_note if related else "",
        }
        if weakest
        else {},
        "share_enabled": bool(report.share_token_hash and not report.share_revoked_at),
    }


def _finding(f: AnalysisFinding) -> dict:
    return {
        "id": str(f.id),
        "category": f.category,
        "severity": f.severity,
        "location": f.location,
        "paragraph": f.paragraph,
        "original_text": f.original_text,
        "explanation": f.explanation,
        "suggestion": f.suggestion,
        "teaching_note": f.teaching_note,
        "example": f.example,
        "improved_sentence": f.improved_sentence,
    }


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
    return _serialize_report(report, page=page, page_size=page_size)


@router.get("/{report_id}/pdf")
def download_pdf(report_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.get(AnalysisReport, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(404, "Report not found.")
    assignment = db.get(Assignment, report.assignment_id) if report.assignment_id else None
    pdf = build_pdf_report(report, assignment.title if assignment else "Assignment")
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=academiccheck-report.pdf"})


@router.post("/{report_id}/share")
def create_share(report_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.get(AnalysisReport, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(404, "Report not found.")
    token = secrets.token_urlsafe(24)
    report.share_token_hash = hash_token(token)
    report.share_revoked_at = None
    db.commit()
    return {"token": token, "path": f"/shared/{token}"}


@router.post("/{report_id}/share/revoke")
def revoke_share(report_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import UTC, datetime

    report = db.get(AnalysisReport, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(404, "Report not found.")
    report.share_revoked_at = datetime.now(UTC)
    db.commit()
    return {"ok": True}


@router.get("/shared/{token}")
def public_share(token: str, db: Session = Depends(get_db)):
    report = db.query(AnalysisReport).filter(AnalysisReport.share_token_hash == hash_token(token)).first()
    if not report or report.share_revoked_at:
        raise HTTPException(404, "This share link is unavailable.")
    return _serialize_report(report, page_size=80)

from sqlalchemy import func, select
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.analysis import AnalysisJob, AnalysisReport
from app.models.assignment import Assignment
from app.models.document import Document
from app.models.user import User
from app.services.entitlements import current_subscription, plan_for

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assignments = db.scalar(
        select(func.count(Assignment.id)).where(Assignment.user_id == user.id, Assignment.deleted_at.is_(None))
    ) or 0
    reports = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.user_id == user.id)
        .order_by(AnalysisReport.created_at.desc())
        .limit(8)
        .all()
    )
    docs = (
        db.query(Document)
        .filter(Document.user_id == user.id, Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
        .limit(6)
        .all()
    )
    avg = db.scalar(select(func.avg(AnalysisReport.overall_score)).where(AnalysisReport.user_id == user.id))
    plan = plan_for(db, user)
    sub, _ = current_subscription(db, user)
    scores = list(
        db.scalars(
            select(AnalysisReport.overall_score)
            .where(AnalysisReport.user_id == user.id)
            .order_by(AnalysisReport.created_at.asc())
            .limit(12)
        )
    )
    return {
        "assignments": assignments,
        "average_score": int(round(avg)) if avg else None,
        "checks_used": sub.checks_used if sub else 0,
        "checks_remaining": max(0, plan.checks_per_month - (sub.checks_used if sub else 0)),
        "plan": plan.name,
        "plan_slug": plan.slug,
        "improvement_trend": scores,
        "recent_reports": [
            {"id": str(r.id), "score": r.overall_score, "summary": r.summary, "created_at": r.created_at.isoformat()}
            for r in reports
        ],
        "recent_documents": [
            {"id": str(d.id), "filename": d.original_filename, "word_count": d.word_count}
            for d in docs
        ],
    }

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.deps import get_current_user, owned_assignment
from app.models.analysis import AnalysisReport
from app.models.user import User
from app.schemas.common import CoachIn
from app.services.ai.enhance import coach_reply
from app.services.entitlements import features_for, plan_for

router = APIRouter(prefix="/api/coach", tags=["coach"])


@router.post("")
def coach(payload: CoachIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_rate_limit(request, "coach", user)
    assignment = owned_assignment(payload.assignment_id, user, db)
    plan = plan_for(db, user)
    feats = features_for(plan)
    if user.is_guest or not feats.get("coach"):
        # Guests and free users get a limited heuristic coach, not a full rewrite.
        pass
    report = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.assignment_id == assignment.id, AnalysisReport.user_id == user.id)
        .order_by(AnalysisReport.created_at.desc())
        .first()
    )
    context = {
        "title": assignment.title,
        "question": assignment.question.raw_text if assignment.question else "",
        "level": assignment.academic_level,
        "score": report.overall_score if report else None,
        "priorities": json.loads(report.priority_actions_json) if report else [],
        "weaknesses": json.loads(report.weaknesses_json) if report else [],
        "disclaimer": "Coach answers use only the student's assignment context and must not invent sources.",
    }
    answer, tokens = coach_reply(payload.question, json.dumps(context))
    return {
        "answer": answer,
        "tokens": tokens,
        "disclaimer": "This coach helps you understand and revise your own work. It will not write the assignment for you.",
    }

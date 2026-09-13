import json
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_field
from app.db.session import get_db_read
from app.deps import get_current_user
from app.models.analysis import AnalysisReport, AnalysisScore
from app.models.assignment import Assignment
from app.models.document import Document
from app.models.user import User
from app.services.credits import available_credits
from app.services.entitlements import current_subscription, features_for, plan_for

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

DIMENSION_ORDER = (
    "relevance",
    "thesis",
    "argument",
    "evidence",
    "structure",
    "academic_writing",
    "citations",
)

DIMENSION_LABELS = {
    "relevance": "Question Relevance",
    "thesis": "Thesis Quality",
    "argument": "Argument Strength",
    "evidence": "Evidence Quality",
    "structure": "Structure",
    "academic_writing": "Writing Quality",
    "grammar": "Writing Quality",
    "citations": "Citation Accuracy",
}

DIMENSION_MERGE = {"grammar": "academic_writing"}


def _safe_actions(raw: str) -> list[str]:
    try:
        data = json.loads(raw or "[]")
        if isinstance(data, list):
            return [str(x) for x in data if str(x).strip()][:6]
    except Exception:
        pass
    return []


def _trend_delta(scores: list[int], window: int) -> int | None:
    if len(scores) < 2:
        return None
    if len(scores) < window * 2:
        return int(round(scores[-1] - scores[0]))
    older = scores[-(window * 2) : -window]
    newer = scores[-window:]
    return int(round((sum(newer) / len(newer)) - (sum(older) / len(older))))


def _norm_category(category: str) -> str:
    return DIMENSION_MERGE.get(category, category)


@router.get("")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db_read)):
    assignments = db.scalar(
        select(func.count(Assignment.id)).where(Assignment.user_id == user.id, Assignment.deleted_at.is_(None))
    ) or 0
    _count, avg = db.execute(
        select(func.count(AnalysisReport.id), func.avg(AnalysisReport.overall_score)).where(
            AnalysisReport.user_id == user.id
        )
    ).one()
    reports = list(
        db.scalars(
            select(AnalysisReport)
            .where(AnalysisReport.user_id == user.id)
            .order_by(AnalysisReport.created_at.desc())
            .limit(12)
        )
    )
    docs = list(
        db.scalars(
            select(Document)
            .where(Document.user_id == user.id, Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
            .limit(6)
        )
    )
    scores = [r.overall_score for r in reversed(reports)]
    sub, subscribed_plan = current_subscription(db, user)
    plan = subscribed_plan if subscribed_plan is not None else plan_for(db, user)
    feats = features_for(plan)

    report_ids = [r.id for r in reports]

    # Single score fetch for all recent reports
    score_rows: list[tuple] = []
    if report_ids:
        score_rows = list(
            db.execute(
                select(AnalysisScore.report_id, AnalysisScore.category, AnalysisScore.score).where(
                    AnalysisScore.report_id.in_(report_ids)
                )
            )
        )

    dim_buckets: dict[str, list[int]] = defaultdict(list)
    by_report: dict = defaultdict(dict)  # report_id -> category -> score
    weakest_by_report: dict = {}
    for rid, cat, sc in score_rows:
        key = _norm_category(cat)
        label = DIMENSION_LABELS.get(key, key.replace("_", " ").title())
        by_report[rid][key] = int(sc)
        if key in DIMENSION_ORDER:
            dim_buckets[key].append(int(sc))
        cur = weakest_by_report.get(rid)
        if cur is None or sc < cur[1]:
            weakest_by_report[rid] = (label, int(sc))

    latest_id = report_ids[0] if report_ids else None
    prev_id = report_ids[1] if len(report_ids) > 1 else None
    latest_map = by_report.get(latest_id, {}) if latest_id else {}
    prev_map = by_report.get(prev_id, {}) if prev_id else {}

    dimensions = []
    for key in DIMENSION_ORDER:
        vals = dim_buckets.get(key) or []
        if not vals:
            continue
        avg_dim = int(round(sum(vals) / len(vals)))
        delta = None
        if key in latest_map and key in prev_map:
            delta = int(latest_map[key] - prev_map[key])
        dimensions.append(
            {
                "category": key,
                "label": DIMENSION_LABELS.get(key, key.replace("_", " ").title()),
                "score": avg_dim,
                "delta": delta,
            }
        )

    weakest = sorted(dimensions, key=lambda d: d["score"])[:3] if dimensions else []
    most_improved = sorted(
        [d for d in dimensions if d.get("delta") is not None],
        key=lambda d: d["delta"] or 0,
        reverse=True,
    )[:3]

    latest = reports[0] if reports else None
    priority_raw = _safe_actions(latest.priority_actions_json) if latest else []
    priority_fixes = []
    for i, title in enumerate(priority_raw[:3]):
        weak = weakest[i] if i < len(weakest) else None
        gap = max(0, 100 - (weak["score"] if weak else 55))
        lift = max(3, min(15, gap // 4 + 4))
        minutes = 5 if lift <= 6 else 10 if lift <= 10 else 15
        priority_fixes.append(
            {
                "id": f"pf-{i}",
                "title": title,
                "impact_score": lift,
                "estimated_improvement": f"+{lift} points",
                "time_required": f"{minutes} minutes",
                "category": weak["category"] if weak else None,
            }
        )
    if not priority_fixes and weakest:
        for i, w in enumerate(weakest[:3]):
            gap = max(0, 100 - w["score"])
            lift = max(3, min(15, gap // 4 + 4))
            minutes = 5 if lift <= 6 else 10 if lift <= 10 else 15
            priority_fixes.append(
                {
                    "id": f"pf-w-{i}",
                    "title": f"Improve {w['label']}",
                    "impact_score": lift,
                    "estimated_improvement": f"+{lift} points",
                    "time_required": f"{minutes} minutes",
                    "category": w["category"],
                }
            )

    report_by_assignment: dict = {}
    for r in reports:
        if r.assignment_id and r.assignment_id not in report_by_assignment:
            report_by_assignment[r.assignment_id] = r

    recent_assignments = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.user_id == user.id, Assignment.deleted_at.is_(None))
            .order_by(Assignment.updated_at.desc())
            .limit(8)
        )
    )

    assignment_rows = []
    for a in recent_assignments:
        r = report_by_assignment.get(a.id)
        weak_label = None
        if r and r.id in weakest_by_report:
            weak_label = weakest_by_report[r.id][0]
        assignment_rows.append(
            {
                "id": str(a.id),
                "title": a.title,
                "status": a.status,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                "score": r.overall_score if r else None,
                "weakest_area": weak_label,
                "report_id": str(r.id) if r else None,
            }
        )

    report_count = int(_count or 0)
    weekly_delta = _trend_delta(scores, 3)
    half = max(1, len(scores) // 2)
    monthly_delta = _trend_delta(scores, 4) if len(scores) >= 8 else _trend_delta(scores, half)

    achievements = [
        {"id": "first_analysis", "title": "First Analysis", "earned": report_count >= 1},
        {"id": "five_analyses", "title": "5 Analyses Completed", "earned": report_count >= 5},
        {
            "id": "improved_thesis",
            "title": "Improved Thesis Score",
            "earned": bool(
                next((d for d in dimensions if d["category"] == "thesis" and (d.get("delta") or 0) > 0), None)
            ),
        },
        {
            "id": "citation_master",
            "title": "Citation Master",
            "earned": bool(next((d for d in dimensions if d["category"] == "citations" and d["score"] >= 80), None)),
        },
    ]

    coach_suggestions = []
    for w in weakest[:3]:
        coach_suggestions.append(
            {
                "id": f"coach-{w['category']}",
                "title": f"Strengthen {w['label']}",
                "body": f"Your average {w['label'].lower()} score is {w['score']}. Ask the coach how to raise it on your next draft.",
            }
        )
    if not coach_suggestions:
        coach_suggestions.append(
            {
                "id": "coach-start",
                "title": "Start with a focused question",
                "body": "After your first check, the coach can walk you through the highest-leverage fixes.",
            }
        )

    first_name = (user.full_name or "").strip().split(" ")[0] if (user.full_name or "").strip() else None
    if user.is_guest and not first_name:
        first_name = "there"

    credits = float(available_credits(db, user))

    return {
        "assignments": assignments,
        "average_score": int(round(avg)) if avg else None,
        "checks_used": sub.checks_used if sub else 0,
        "checks_remaining": max(0, plan.checks_per_month - (sub.checks_used if sub else 0)),
        "checks_per_month": plan.checks_per_month,
        "plan": plan.name,
        "plan_slug": plan.slug,
        "improvement_trend": scores,
        "recent_reports": [
            {
                "id": str(r.id),
                "score": r.overall_score,
                "summary": decrypt_field(r.summary),
                "created_at": r.created_at.isoformat(),
                "assignment_id": str(r.assignment_id) if r.assignment_id else None,
            }
            for r in reports[:8]
        ],
        "recent_documents": [
            {"id": str(d.id), "filename": d.original_filename, "word_count": d.word_count} for d in docs
        ],
        "user": {
            "full_name": user.full_name or "",
            "first_name": first_name or "Scholar",
            "is_guest": user.is_guest,
            "academic_level": user.academic_level,
        },
        "report_count": report_count,
        "weekly_delta": weekly_delta,
        "monthly_delta": monthly_delta,
        "dimensions": dimensions,
        "most_improved": most_improved,
        "priority_fixes": priority_fixes,
        "recent_assignments": assignment_rows,
        "achievements": achievements,
        "coach_suggestions": coach_suggestions,
        "credits": credits,
        "features": {
            "coach": bool(feats.get("coach")),
            "pdf_report": bool(feats.get("pdf_report")),
            "compare": bool(feats.get("compare")),
            "full_analysis": bool(feats.get("full_analysis")),
            "citation_verify": bool(feats.get("citation_verify")),
        },
    }

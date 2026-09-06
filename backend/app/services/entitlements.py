from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.analysis import AnalysisJob
from app.models.billing import Plan, Subscription
from app.models.user import User

DEFAULT_FEATURES = {
    "free": {
        "grammar": True,
        "structure": True,
        "question": True,
        "basic_feedback": True,
        "full_analysis": False,
        "rubric": False,
        "compare": False,
        "coach": False,
        "ai_indicator": False,
        "pdf_report": False,
        "citation_verify": False,
        "history": False,
    },
    "student": {
        "grammar": True,
        "structure": True,
        "question": True,
        "basic_feedback": True,
        "full_analysis": True,
        "rubric": False,
        "compare": False,
        "coach": False,
        "ai_indicator": False,
        "pdf_report": False,
        "citation_verify": False,
        "history": True,
    },
    "pro": {
        "grammar": True,
        "structure": True,
        "question": True,
        "basic_feedback": True,
        "full_analysis": True,
        "rubric": True,
        "compare": True,
        "coach": True,
        "ai_indicator": True,
        "pdf_report": True,
        "citation_verify": True,
        "history": True,
    },
    "power": {
        "grammar": True,
        "structure": True,
        "question": True,
        "basic_feedback": True,
        "full_analysis": True,
        "rubric": True,
        "compare": True,
        "coach": True,
        "ai_indicator": True,
        "pdf_report": True,
        "citation_verify": True,
        "history": True,
        "priority": True,
    },
}


def current_subscription(db: Session, user: User) -> tuple[Subscription | None, Plan | None]:
    sub = db.scalar(
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status.in_(("active", "trialing", "past_due")))
        .order_by(Subscription.created_at.desc())
    )
    return sub, sub.plan if sub else None


def plan_for(db: Session, user: User) -> Plan:
    _sub, plan = current_subscription(db, user)
    if plan:
        return plan
    slug = "free" if not user.is_guest else "free"
    plan = db.scalar(select(Plan).where(Plan.slug == slug))
    if plan:
        return plan
    return Plan(
        slug="free",
        name="Free",
        checks_per_month=get_settings().guest_max_checks,
        max_words=get_settings().guest_max_words,
        features=DEFAULT_FEATURES["free"],
    )


def features_for(plan: Plan) -> dict:
    base = DEFAULT_FEATURES.get(plan.slug, DEFAULT_FEATURES["free"])
    merged = {**base, **(plan.features or {})}
    return merged


def assert_can_analyze(db: Session, user: User, word_count: int, analysis_type: str = "full") -> Plan:
    plan = plan_for(db, user)
    max_words = plan.max_words
    if user.is_guest:
        max_words = min(max_words, get_settings().guest_max_words)
    if word_count > max_words:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"This document is {word_count} words. Your current plan allows up to {max_words} words.",
        )
    used = _checks_used_this_period(db, user)
    limit = plan.checks_per_month if not user.is_guest else get_settings().guest_max_checks
    if used >= limit:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "You have used the checks included in your current plan. Upgrade or wait for the next period.",
        )
    feats = features_for(plan)
    if analysis_type in {"full", "academic"} and not feats.get("full_analysis") and not user.is_guest:
        if analysis_type == "full" and plan.slug == "free":
            # Free users still get a basic check; the runner will downgrade modules.
            return plan
    if analysis_type == "rubric" and not feats.get("rubric"):
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Rubric analysis is available on Pro and above.")
    return plan


def increment_usage(db: Session, user: User) -> None:
    sub, _plan = current_subscription(db, user)
    if sub:
        if sub.current_period_end and sub.current_period_end < datetime.now(UTC):
            sub.checks_used = 0
            sub.current_period_start = datetime.now(UTC)
            sub.current_period_end = datetime.now(UTC)
        sub.checks_used = (sub.checks_used or 0) + 1


def _checks_used_this_period(db: Session, user: User) -> int:
    sub, _plan = current_subscription(db, user)
    if sub and sub.current_period_start:
        start = sub.current_period_start
        return db.scalar(
            select(func.count(AnalysisJob.id)).where(
                AnalysisJob.user_id == user.id,
                AnalysisJob.created_at >= start,
                AnalysisJob.status.in_(("queued", "processing", "completed")),
            )
        ) or 0
    start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count(AnalysisJob.id)).where(
            AnalysisJob.user_id == user.id,
            AnalysisJob.created_at >= start,
            AnalysisJob.status.in_(("queued", "processing", "completed")),
        )
    ) or 0

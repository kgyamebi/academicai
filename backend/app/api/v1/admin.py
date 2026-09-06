from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_roles
from app.models.admin import AdminAuditLog, FeatureFlag
from app.models.analysis import AnalysisJob
from app.models.billing import Payment, Plan
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
def overview(admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return {
        "users": db.scalar(select(func.count(User.id)).where(User.is_guest.is_(False))) or 0,
        "jobs": db.scalar(select(func.count(AnalysisJob.id))) or 0,
        "failed_jobs": db.scalar(select(func.count(AnalysisJob.id)).where(AnalysisJob.status == "failed")) or 0,
        "payments": db.scalar(select(func.count(Payment.id)).where(Payment.status == "successful")) or 0,
        "token_usage": db.scalar(select(func.coalesce(func.sum(AnalysisJob.token_usage), 0))) or 0,
    }


@router.get("/users")
def users(
    q: str = "",
    page: int = Query(1, ge=1),
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    query = select(User).where(User.is_guest.is_(False))
    if q:
        query = query.where(User.email.ilike(f"%{q}%"))
    items = db.scalars(query.order_by(User.created_at.desc()).offset((page - 1) * 20).limit(20)).all()
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "is_suspended": u.is_suspended,
                "role": u.role.name if u.role else None,
            }
            for u in items
        ]
    }


@router.post("/users/{user_id}/suspend")
def suspend(user_id: str, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    from uuid import UUID

    user = db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(404, "User not found.")
    user.is_suspended = True
    db.add(AdminAuditLog(admin_user_id=admin.id, action="suspend_user", target_type="user", target_id=user_id))
    db.commit()
    return {"ok": True}


@router.get("/plans")
def plans(admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    items = db.scalars(select(Plan).order_by(Plan.sort_order)).all()
    return {
        "items": [
            {
                "id": str(p.id),
                "slug": p.slug,
                "name": p.name,
                "price_usd_cents": p.price_usd_cents,
                "checks_per_month": p.checks_per_month,
                "max_words": p.max_words,
                "features": p.features,
                "is_active": p.is_active,
            }
            for p in items
        ]
    }


@router.patch("/plans/{plan_id}")
def update_plan(plan_id: str, payload: dict, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    from uuid import UUID

    plan = db.get(Plan, UUID(plan_id))
    if not plan:
        raise HTTPException(404, "Plan not found.")
    for field in ("name", "price_usd_cents", "checks_per_month", "max_words", "features", "is_active", "description"):
        if field in payload:
            setattr(plan, field, payload[field])
    db.add(AdminAuditLog(admin_user_id=admin.id, action="update_plan", target_type="plan", target_id=plan_id))
    db.commit()
    return {"ok": True}


@router.get("/flags")
def flags(admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    items = db.scalars(select(FeatureFlag)).all()
    return {"items": [{"key": f.key, "enabled": f.enabled, "description": f.description} for f in items]}


@router.post("/flags")
def upsert_flag(payload: dict, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    flag = db.scalar(select(FeatureFlag).where(FeatureFlag.key == payload["key"]))
    if not flag:
        flag = FeatureFlag(key=payload["key"], enabled=bool(payload.get("enabled", True)), description=payload.get("description", ""))
        db.add(flag)
    else:
        flag.enabled = bool(payload.get("enabled", flag.enabled))
    db.commit()
    return {"ok": True}

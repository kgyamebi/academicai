from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import create_token, decode_token, hash_password, hash_token, verify_password
from app.models.billing import Plan, Subscription
from app.models.user import Role, SessionToken, User
from app.services.emailer import send_email


def get_role(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if role:
        return role
    role = Role(name=name, description=name)
    db.add(role)
    db.flush()
    return role


def register_user(db: Session, email: str, password: str, full_name: str, country: str | None = None) -> User:
    existing = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if existing and not existing.is_guest:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = existing or User(email=email.lower())
    user.password_hash = hash_password(password)
    user.full_name = full_name
    user.country = country
    user.is_guest = False
    user.is_active = True
    user.role = get_role(db, "student")
    db.add(user)
    db.flush()
    _ensure_free_subscription(db, user)
    token = create_token(str(user.id), "verify")
    send_email(
        user.email,
        "Verify your AcademicCheck AI account",
        f"Welcome to AcademicCheck AI.\n\nVerify your email: {get_settings().app_web_url}/verify?token={token}\n",
    )
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if not user or user.is_guest or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    if user.is_suspended or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not active.")
    user.last_login_at = datetime.now(UTC)
    return user


def issue_session(db: Session, user: User, user_agent: str | None, ip: str | None) -> dict:
    settings = get_settings()
    access = create_token(str(user.id), "access", extra={"role": user.role.name if user.role else "student"})
    refresh = create_token(str(user.id), "refresh")
    db.add(
        SessionToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            token_type="refresh",
            user_agent=user_agent,
            ip_address=ip,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


def refresh_session(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.") from exc
    if payload.get("typ") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session.")
    row = db.scalar(select(SessionToken).where(SessionToken.token_hash == hash_token(refresh_token)))
    if not row or row.revoked_at or row.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.")
    user = db.get(User, UUID(payload["sub"]))
    if not user or user.deleted_at or user.is_suspended:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account unavailable.")
    return issue_session(db, user, row.user_agent, row.ip_address)


def logout(db: Session, refresh_token: str | None) -> None:
    if not refresh_token:
        return
    row = db.scalar(select(SessionToken).where(SessionToken.token_hash == hash_token(refresh_token)))
    if row:
        row.revoked_at = datetime.now(UTC)


def create_guest(db: Session, ip: str | None) -> tuple[User, dict]:
    user = User(
        email=f"guest-{datetime.now(UTC).timestamp()}@guest.academiccheck.local",
        is_guest=True,
        full_name="Guest",
        role=get_role(db, "guest"),
    )
    db.add(user)
    db.flush()
    tokens = issue_session(db, user, "guest", ip)
    tokens["access_token"] = create_token(str(user.id), "guest", extra={"role": "guest"})
    return user, tokens


def request_password_reset(db: Session, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if not user or user.is_guest:
        return
    token = create_token(str(user.id), "reset")
    send_email(
        user.email,
        "Reset your AcademicCheck AI password",
        f"Reset your password: {get_settings().app_web_url}/reset-password?token={token}\n",
    )


def reset_password(db: Session, token: str, new_password: str) -> None:
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid or expired.") from exc
    if payload.get("typ") != "reset":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid or expired.")
    user = db.get(User, UUID(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid or expired.")
    user.password_hash = hash_password(new_password)


def verify_email(db: Session, token: str) -> None:
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This verification link is invalid or expired.") from exc
    if payload.get("typ") != "verify":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This verification link is invalid or expired.")
    user = db.get(User, UUID(payload["sub"]))
    if user:
        user.email_verified_at = datetime.now(UTC)


def serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email if not user.is_guest else None,
        "full_name": user.full_name,
        "is_guest": user.is_guest,
        "role": user.role.name if user.role else "student",
        "country": user.country,
        "academic_level": user.academic_level,
        "email_verified": bool(user.email_verified_at),
        "training_opt_in": user.training_opt_in,
    }


def _ensure_free_subscription(db: Session, user: User) -> None:
    existing = db.scalar(
        select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active")
    )
    if existing:
        return
    plan = db.scalar(select(Plan).where(Plan.slug == "free"))
    if not plan:
        return
    db.add(
        Subscription(
            user_id=user.id,
            plan_id=plan.id,
            status="active",
            provider="internal",
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC) + timedelta(days=30),
        )
    )

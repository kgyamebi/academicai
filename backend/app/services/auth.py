from __future__ import annotations

import secrets
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import (
    create_token,
    decode_token,
    dummy_password_check,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_password,
)
from app.core.time import is_past, utcnow
from app.models.billing import Plan, Subscription
from app.models.user import Role, SessionToken, User
from app.services.email_templates import (
    email_change_verify,
    email_changed_notice,
    password_reset_email,
    verification_email,
    verification_success_email,
)
from app.services.email_validation import validate_registration_email
from app.services.emailer import send_email
from app.services.security_events import record_security_event

LOCKOUT_ATTEMPTS = 8
LOCKOUT_MINUTES = 15


def get_role(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if role:
        return role
    role = Role(name=name, description=name)
    db.add(role)
    db.flush()
    return role


def assert_email_verified(user: User) -> None:
    """Invoice App pattern: signup/login stay open; gate privileged actions."""
    if user.is_guest:
        return
    if not get_settings().require_email_verification:
        return
    if user.email_verified_at:
        return
    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "Verify your email to unlock this feature. Open Settings or use Resend verification.",
    )


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    country: str | None = None,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    try:
        email_norm = validate_registration_email(email)
    except HTTPException as exc:
        if "disposable" in str(exc.detail).lower() or "temporary" in str(exc.detail).lower():
            record_security_event(
                db,
                "disposable_email_attempt",
                ip_address=ip,
                user_agent=user_agent,
                details=email[:120],
                severity="warning",
            )
        raise

    existing = db.scalar(select(User).where(User.email == email_norm, User.deleted_at.is_(None)))
    if existing and not existing.is_guest:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = existing or User(email=email_norm)
    user.password_hash = hash_password(password)
    user.full_name = full_name
    user.country = country
    user.is_guest = False
    user.is_active = True
    user.email_verified_at = None
    user.pending_email = None
    user.role = get_role(db, "student")
    db.add(user)
    db.flush()
    _ensure_free_subscription(db, user)
    _issue_verification_email(db, user)
    record_security_event(
        db,
        "account_created",
        user_id=user.id,
        ip_address=ip,
        user_agent=user_agent,
        details="registration",
    )
    record_security_event(db, "verification_sent", user_id=user.id, ip_address=ip)
    return user


def authenticate(
    db: Session,
    email: str,
    password: str,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    user = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if not user or user.is_guest or not user.password_hash:
        dummy_password_check(password)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")

    if user.locked_until and not is_past(user.locked_until):
        record_security_event(db, "login_locked", user_id=user.id, ip_address=ip, user_agent=user_agent, severity="warning")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is temporarily locked. Try again later.")
    if user.is_suspended or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not active.")
    if not verify_password(password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= LOCKOUT_ATTEMPTS:
            user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            record_security_event(db, "account_lockout", user_id=user.id, ip_address=ip, severity="warning")
        record_security_event(db, "login_failed", user_id=user.id, ip_address=ip, user_agent=user_agent, severity="warning")
        db.flush()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    # Invoice pattern: allow login while unverified; client shows banner; privileged APIs call assert_email_verified.
    previous_sessions = list(user.sessions)
    known_ips = {s.ip_address for s in previous_sessions if s.ip_address}
    if ip and known_ips and ip not in known_ips:
        record_security_event(
            db,
            "login_new_ip",
            user_id=user.id,
            ip_address=ip,
            user_agent=user_agent,
            details="Sign-in from a new IP address.",
            severity="warning",
        )
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    record_security_event(db, "login_success", user_id=user.id, ip_address=ip, user_agent=user_agent)
    return user


def issue_session(db: Session, user: User, user_agent: str | None, ip: str | None) -> dict:
    settings = get_settings()
    _enforce_refresh_session_limit(db, user.id, limit=max(1, int(settings.max_refresh_sessions)))
    access = create_token(str(user.id), "access", extra={"role": user.role.name if user.role else "student"})
    refresh = create_token(str(user.id), "refresh")
    db.add(
        SessionToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            token_type="refresh",
            user_agent=user_agent,
            ip_address=ip,
            expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


def _enforce_refresh_session_limit(db: Session, user_id: UUID, *, limit: int) -> None:
    active = list(
        db.scalars(
            select(SessionToken)
            .where(
                SessionToken.user_id == user_id,
                SessionToken.token_type == "refresh",
                SessionToken.revoked_at.is_(None),
            )
            .order_by(SessionToken.created_at.asc())
        ).all()
    )
    overflow = len(active) - (limit - 1)
    if overflow <= 0:
        return
    now = utcnow()
    for row in active[:overflow]:
        row.revoked_at = now
    record_security_event(
        db,
        "session_limit_enforced",
        user_id=user_id,
        details=f"revoked={overflow} limit={limit}",
        severity="info",
    )


def refresh_session(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.") from exc
    if payload.get("typ") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session.")
    row = db.scalar(
        select(SessionToken)
        .where(SessionToken.token_hash == hash_token(refresh_token), SessionToken.token_type == "refresh")
        .with_for_update()
    )
    if not row:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.")
    if row.revoked_at:
        _revoke_all_sessions(db, row.user_id)
        record_security_event(
            db,
            "refresh_reuse",
            user_id=row.user_id,
            details="Refresh token reuse detected; all sessions revoked.",
            severity="critical",
        )
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.")
    if is_past(row.expires_at):
        row.revoked_at = utcnow()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.")
    user = db.get(User, UUID(payload["sub"]))
    if not user or user.deleted_at or user.is_suspended or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account unavailable.")
    row.revoked_at = utcnow()
    return issue_session(db, user, row.user_agent, row.ip_address)


def logout(db: Session, refresh_token: str | None) -> None:
    if not refresh_token:
        return
    row = db.scalar(select(SessionToken).where(SessionToken.token_hash == hash_token(refresh_token)))
    if row:
        row.revoked_at = utcnow()


def revoke_all_sessions(db: Session, user_id: UUID) -> None:
    _revoke_all_sessions(db, user_id)


def create_guest(db: Session, ip: str | None) -> tuple[User, dict]:
    user = User(
        email=f"guest-{utcnow().timestamp()}@guest.academiccheck.local",
        is_guest=True,
        full_name="Guest",
        role=get_role(db, "guest"),
    )
    db.add(user)
    db.flush()
    tokens = issue_session(db, user, "guest", ip)
    tokens["access_token"] = create_token(str(user.id), "guest", extra={"role": "guest"})
    return user, tokens


def request_password_reset(db: Session, email: str, *, ip: str | None = None) -> None:
    """Enumeration-safe. Verified users get reset; unverified get a fresh verification email."""
    user = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if not user or user.is_guest:
        return
    settings = get_settings()
    if settings.require_verified_for_password_reset and not user.email_verified_at:
        _issue_verification_email(db, user, force=True)
        record_security_event(db, "password_reset_blocked_unverified", user_id=user.id, ip_address=ip)
        record_security_event(db, "verification_sent", user_id=user.id, ip_address=ip, details="via_password_reset")
        return
    _invalidate_tokens(db, user.id, "reset")
    raw = _new_opaque_token()
    _store_one_time_token(db, user.id, raw, "reset")
    hours = settings.password_reset_hours
    subject, html, text = password_reset_email(
        url=f"{settings.app_web_url.rstrip('/')}/reset-password?token={raw}",
        hours=hours,
    )
    send_email(user.email, subject, text, html=html)
    record_security_event(db, "password_reset_requested", user_id=user.id, ip_address=ip)


def reset_password(db: Session, token: str, new_password: str) -> None:
    user_id = _consume_opaque_token(db, token, "reset")
    if not user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid or expired.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid or expired.")
    user.password_hash = hash_password(new_password)
    user.failed_login_count = 0
    user.locked_until = None
    _revoke_all_sessions(db, user.id)
    record_security_event(db, "password_reset_completed", user_id=user.id)


def verify_email(db: Session, token: str, *, ip: str | None = None) -> dict:
    user_id = _consume_opaque_token(db, token, "verify")
    if not user_id:
        record_security_event(db, "verification_failed", ip_address=ip, details="invalid_or_expired", severity="warning")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This verification link is invalid or expired.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This verification link is invalid or expired.")
    if user.pending_email:
        user.email = user.pending_email
        user.pending_email = None
    user.email_verified_at = utcnow()
    _invalidate_tokens(db, user.id, "verify")
    subject, html, text = verification_success_email(name=user.full_name)
    send_email(user.email, subject, text, html=html)
    record_security_event(db, "verification_completed", user_id=user.id, ip_address=ip)
    return {"ok": True, "email": user.email, "email_verified": True}


def resend_verification(db: Session, user: User, *, ip: str | None = None) -> dict:
    if user.is_guest:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Guest accounts do not require email verification.")
    if user.email_verified_at and not user.pending_email:
        return {"ok": True, "already_verified": True}
    settings = get_settings()
    if user.verification_sent_at and not is_past(
        user.verification_sent_at + timedelta(seconds=max(15, settings.email_resend_cooldown_seconds))
    ):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Please wait a moment before requesting another verification email.",
        )
    _issue_verification_email(db, user, force=True)
    record_security_event(db, "verification_resent", user_id=user.id, ip_address=ip)
    return {"ok": True}


def change_email(db: Session, user: User, new_email: str, *, ip: str | None = None) -> dict:
    if user.is_guest:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Guest accounts cannot change email.")
    email_norm = validate_registration_email(new_email)
    if email_norm == user.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That is already your email address.")
    taken = db.scalar(select(User).where(User.email == email_norm, User.deleted_at.is_(None), User.id != user.id))
    if taken:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    old = user.email
    user.pending_email = email_norm
    user.email_verified_at = None
    subject_old, html_old, text_old = email_changed_notice(old_email=old, new_email=email_norm)
    send_email(old, subject_old, text_old, html=html_old)
    _issue_verification_email(db, user, force=True, to_email=email_norm)
    record_security_event(db, "email_changed", user_id=user.id, ip_address=ip, details=f"{old}->{email_norm}")
    record_security_event(db, "verification_sent", user_id=user.id, ip_address=ip, details="email_change")
    return {"ok": True, "email": old, "pending_email": email_norm, "email_verified": False}


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
        "pending_email": user.pending_email,
        "verification_sent_at": user.verification_sent_at.isoformat() if user.verification_sent_at else None,
        "training_opt_in": user.training_opt_in,
        "mfa_enabled": bool(user.mfa_enabled),
    }


def _ensure_free_subscription(db: Session, user: User) -> None:
    existing = db.scalar(select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active"))
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
            current_period_start=utcnow(),
            current_period_end=utcnow() + timedelta(days=30),
        )
    )


def _revoke_all_sessions(db: Session, user_id: UUID) -> None:
    now = utcnow()
    for row in db.scalars(
        select(SessionToken).where(
            SessionToken.user_id == user_id,
            SessionToken.token_type == "refresh",
            SessionToken.revoked_at.is_(None),
        )
    ):
        row.revoked_at = now


def _new_opaque_token() -> str:
    return secrets.token_urlsafe(32)


def _invalidate_tokens(db: Session, user_id: UUID, token_type: str) -> None:
    now = utcnow()
    for row in db.scalars(
        select(SessionToken).where(
            SessionToken.user_id == user_id,
            SessionToken.token_type == token_type,
            SessionToken.revoked_at.is_(None),
        )
    ):
        row.revoked_at = now


def _store_one_time_token(db: Session, user_id: UUID, token: str, token_type: str) -> None:
    settings = get_settings()
    hours = settings.password_reset_hours if token_type == "reset" else settings.email_verification_hours
    db.add(
        SessionToken(
            user_id=user_id,
            token_hash=hash_token(token),
            token_type=token_type,
            expires_at=utcnow() + timedelta(hours=hours),
        )
    )


def _consume_opaque_token(db: Session, token: str, token_type: str) -> UUID | None:
    """Invoice-style single-use claim via revoke. Supports legacy JWT verify/reset tokens briefly."""
    row = db.scalar(
        select(SessionToken)
        .where(SessionToken.token_hash == hash_token(token), SessionToken.token_type == token_type)
        .with_for_update()
    )
    if row and not row.revoked_at and not is_past(row.expires_at):
        row.revoked_at = utcnow()
        return row.user_id
    # Legacy JWT tokens issued before opaque migration
    try:
        payload = decode_token(token)
        if payload.get("typ") != token_type:
            return None
        if not _consume_one_time_token_legacy(db, token, token_type):
            return None
        return UUID(payload["sub"])
    except Exception:
        return None


def _consume_one_time_token_legacy(db: Session, token: str, token_type: str) -> bool:
    row = db.scalar(
        select(SessionToken).where(
            SessionToken.token_hash == hash_token(token),
            SessionToken.token_type == token_type,
        )
    )
    if not row or row.revoked_at or is_past(row.expires_at):
        return False
    row.revoked_at = utcnow()
    return True


def _issue_verification_email(
    db: Session,
    user: User,
    *,
    force: bool = False,
    to_email: str | None = None,
) -> None:
    settings = get_settings()
    _invalidate_tokens(db, user.id, "verify")
    raw = _new_opaque_token()
    _store_one_time_token(db, user.id, raw, "verify")
    user.verification_sent_at = utcnow()
    hours = settings.email_verification_hours
    target = to_email or user.pending_email or user.email
    url = f"{settings.app_web_url.rstrip('/')}/verify-email?token={raw}"
    if user.pending_email:
        subject, html, text = email_change_verify(name=user.full_name, url=url, hours=hours)
    else:
        subject, html, text = verification_email(name=user.full_name, url=url, hours=hours)
    send_email(target, subject, text, html=html)
    if force:
        db.flush()

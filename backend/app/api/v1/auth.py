import secrets

from fastapi import APIRouter, Body, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies, set_csrf_cookie
from app.core.logging import get_logger
from app.core.rate_limit import check_rate_limit
from app.core.time import utcnow
from app.db.session import get_db
from app.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.common import (
    LoginIn,
    PasswordResetIn,
    PasswordResetRequestIn,
    RefreshIn,
    RegisterIn,
    TokenResponse,
    VerifyIn,
)
from app.services import auth as auth_service

log = get_logger("auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookies(response: Response, tokens: dict) -> dict:
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"], secrets.token_urlsafe(32))
    return tokens


@router.get("/csrf")
def csrf(response: Response):
    token = secrets.token_urlsafe(32)
    set_csrf_cookie(response, token)
    return {"csrf_token": token}


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    check_rate_limit(request, "signup")
    user = auth_service.register_user(
        db,
        payload.email,
        payload.password,
        payload.full_name,
        payload.country,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    tokens = auth_service.issue_session(
        db, user, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    db.commit()
    return _set_session_cookies(response, tokens)


@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    check_rate_limit(request, "login")
    try:
        user = auth_service.authenticate(
            db,
            payload.email,
            payload.password,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        db.commit()
        raise
    from app.services import mfa as mfa_service

    # Privileged accounts must enroll MFA before a full session; return enroll token (no access cookies).
    if mfa_service.role_name(user) in mfa_service.PRIVILEGED_ROLES and not user.mfa_enabled:
        enroll = mfa_service.issue_mfa_enroll_challenge(user)
        db.commit()
        return {
            "mfa_enrollment_required": True,
            "mfa_enroll_token": enroll,
            "user": {"id": str(user.id), "email": user.email, "mfa_enabled": False},
        }
    if user.mfa_enabled:
        challenge = mfa_service.issue_mfa_challenge(user)
        db.commit()
        return {
            "mfa_required": True,
            "mfa_challenge_token": challenge,
            "user": {"id": str(user.id), "email": user.email, "mfa_enabled": True},
        }
    tokens = auth_service.issue_session(
        db, user, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    db.commit()
    return _set_session_cookies(response, tokens)


def _mfa_actor(db: Session, user: User | None, payload: dict | None) -> User:
    from app.services import mfa as mfa_service

    enroll = str((payload or {}).get("mfa_enroll_token") or "")
    if enroll:
        return mfa_service.user_from_enroll_token(db, enroll)
    if user is None:
        from fastapi import HTTPException, status

        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in.")
    return user


@router.post("/mfa/setup")
def mfa_setup(
    payload: dict | None = Body(default=None),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    from app.services import mfa as mfa_service

    actor = _mfa_actor(db, user, payload)
    result = mfa_service.setup_totp(db, actor)
    db.commit()
    return result


@router.post("/mfa/enable")
def mfa_enable(
    payload: dict = Body(...),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    from app.services import mfa as mfa_service

    actor = _mfa_actor(db, user, payload)
    result = mfa_service.enable_totp(db, actor, str(payload.get("code") or ""))
    db.commit()
    return result


@router.post("/mfa/disable")
def mfa_disable(payload: dict = Body(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services import mfa as mfa_service

    mfa_service.disable_totp(db, user, str(payload.get("code") or ""))
    db.commit()
    return {"enabled": False}


@router.post("/mfa/verify")
def mfa_verify(
    request: Request,
    response: Response,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "login")
    from app.services import mfa as mfa_service

    user = mfa_service.complete_mfa_challenge(
        db, str(payload.get("mfa_challenge_token") or ""), str(payload.get("code") or "")
    )
    tokens = auth_service.issue_session(
        db, user, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    db.commit()
    return _set_session_cookies(response, tokens)


@router.post("/guest", response_model=TokenResponse)
def guest(request: Request, response: Response, db: Session = Depends(get_db)):
    check_rate_limit(request, "signup")
    _user, tokens = auth_service.create_guest(db, request.client.host if request.client else None)
    db.commit()
    return _set_session_cookies(response, tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    payload: RefreshIn | None = Body(default=None),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "login")
    token = (payload.refresh_token if payload else None) or request.cookies.get(REFRESH_COOKIE)
    if not token:
        from fastapi import HTTPException, status

        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.")
    tokens = auth_service.refresh_session(db, token)
    db.commit()
    return _set_session_cookies(response, tokens)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    payload: RefreshIn | None = Body(default=None),
    db: Session = Depends(get_db),
):
    token = (payload.refresh_token if payload else None) or request.cookies.get(REFRESH_COOKIE)
    auth_service.logout(db, token)
    db.commit()
    clear_auth_cookies(response)
    return {"ok": True}


@router.post("/password/forgot")
def forgot(payload: PasswordResetRequestIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "password_forgot")
    auth_service.request_password_reset(
        db, payload.email, ip=request.client.host if request.client else None
    )
    db.commit()
    # Enumeration-safe wording (Invoice App pattern).
    return {"ok": True, "message": "If an account exists for that email, we sent instructions."}


@router.post("/logout-all")
def logout_all(request: Request, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service.revoke_all_sessions(db, user.id)
    db.commit()
    clear_auth_cookies(response)
    return {"ok": True}


@router.post("/password/reset")
def reset(payload: PasswordResetIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "login")
    auth_service.reset_password(db, payload.token, payload.password)
    db.commit()
    return {"ok": True}


@router.post("/verify")
@router.post("/verify-email")
def verify(payload: VerifyIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "login")
    result = auth_service.verify_email(db, payload.token, ip=request.client.host if request.client else None)
    db.commit()
    return result


@router.post("/resend-verification")
def resend_verification(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_rate_limit(request, "verify", user)
    result = auth_service.resend_verification(db, user, ip=request.client.host if request.client else None)
    db.commit()
    return result


@router.post("/email/change")
def change_email(
    request: Request,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "verify", user)
    email = str(payload.get("email") or "")
    result = auth_service.change_email(db, user, email, ip=request.client.host if request.client else None)
    db.commit()
    return result


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return auth_service.serialize_user(user)


@router.delete("/me")
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.assignment import Assignment
    from app.models.billing import Subscription
    from app.models.document import Document
    from app.services.documents.storage import delete_bytes

    user.is_active = False
    user.deletion_requested_at = utcnow()
    user.email = f"deleted-{user.id}@deleted.academiccheck.local"
    user.password_hash = None
    user.full_name = "Deleted user"
    for assignment in db.query(Assignment).filter(Assignment.user_id == user.id).all():
        assignment.deleted_at = utcnow()
        assignment.title = "Deleted assignment"
        if assignment.question:
            assignment.question.raw_text = ""
    for document in db.query(Document).filter(Document.user_id == user.id).all():
        document.deleted_at = utcnow()
        document.extracted_text = ""
        document.normalized_text = ""
        try:
            delete_bytes(document.storage_key)
        except Exception as exc:  # noqa: BLE001
            log.error("account_delete_storage_failed", error=str(exc))
    for sub in db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(("active", "past_due", "trialing")),
    ).all():
        sub.status = "cancelled"
        sub.cancel_at_period_end = True
        sub.cancelled_at = utcnow()
    auth_service.revoke_all_sessions(db, user.id)
    db.commit()
    return {"ok": True, "note": "Financial records required by law may be retained."}

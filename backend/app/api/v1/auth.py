from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.deps import get_current_user
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

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "signup")
    user = auth_service.register_user(db, payload.email, payload.password, payload.full_name, payload.country)
    tokens = auth_service.issue_session(db, user, request.headers.get("user-agent"), request.client.host if request.client else None)
    db.commit()
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "login")
    user = auth_service.authenticate(db, payload.email, payload.password)
    tokens = auth_service.issue_session(db, user, request.headers.get("user-agent"), request.client.host if request.client else None)
    db.commit()
    return tokens


@router.post("/guest", response_model=TokenResponse)
def guest(request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "signup")
    _user, tokens = auth_service.create_guest(db, request.client.host if request.client else None)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshIn, db: Session = Depends(get_db)):
    tokens = auth_service.refresh_session(db, payload.refresh_token)
    db.commit()
    return tokens


@router.post("/logout")
def logout(payload: RefreshIn, db: Session = Depends(get_db)):
    auth_service.logout(db, payload.refresh_token)
    db.commit()
    return {"ok": True}


@router.post("/password/forgot")
def forgot(payload: PasswordResetRequestIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, "login")
    auth_service.request_password_reset(db, payload.email)
    db.commit()
    return {"ok": True}


@router.post("/password/reset")
def reset(payload: PasswordResetIn, db: Session = Depends(get_db)):
    auth_service.reset_password(db, payload.token, payload.password)
    db.commit()
    return {"ok": True}


@router.post("/verify")
def verify(payload: VerifyIn, db: Session = Depends(get_db)):
    auth_service.verify_email(db, payload.token)
    db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return auth_service.serialize_user(user)


@router.delete("/me")
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import UTC, datetime

    from app.models.assignment import Assignment
    from app.models.document import Document
    from app.services.documents.storage import delete_bytes

    user.is_active = False
    user.deletion_requested_at = datetime.now(UTC)
    user.email = f"deleted-{user.id}@deleted.academiccheck.local"
    user.password_hash = None
    user.full_name = "Deleted user"
    for assignment in db.query(Assignment).filter(Assignment.user_id == user.id).all():
        assignment.deleted_at = datetime.now(UTC)
        assignment.title = "Deleted assignment"
        if assignment.question:
            assignment.question.raw_text = ""
    for document in db.query(Document).filter(Document.user_id == user.id).all():
        document.deleted_at = datetime.now(UTC)
        document.extracted_text = ""
        document.normalized_text = ""
        try:
            delete_bytes(document.storage_key)
        except Exception:
            pass
    db.commit()
    return {"ok": True, "note": "Financial records required by law may be retained."}

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.cookies import ACCESS_COOKIE
from app.core.security import decode_token
from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.document import Document
from app.models.user import User


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    ac_access: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
) -> User:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    elif ac_access:
        token = ac_access
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in.")
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Please sign in again.") from exc
    if payload.get("typ") not in {"access", "guest"}:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token.")
    user = db.get(User, UUID(payload["sub"]))
    if not user or user.deleted_at or user.is_suspended or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account unavailable.")
    request.state.user = user
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    ac_access: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
) -> User | None:
    if not authorization and not ac_access:
        return None
    try:
        return get_current_user(request, db, authorization, ac_access)
    except HTTPException:
        return None


def require_roles(*roles: str) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        name = user.role.name if user.role else "student"
        if name not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this action.")
        return user

    return checker


def owned_assignment(assignment_id: UUID, user: User, db: Session) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if not assignment or assignment.deleted_at or assignment.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found.")
    return assignment


def owned_document(document_id: UUID, user: User, db: Session) -> Document:
    document = db.get(Document, document_id)
    if not document or document.deleted_at or document.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")
    return document

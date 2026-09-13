"""Lab simulated attacks — repository evidence only. Not an independent pentest."""

from __future__ import annotations

import jwt
from sqlalchemy import select

from app.config import get_settings
from app.core.security import assert_password_policy, decode_token, hash_password
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.user import SessionToken, User
from app.services import auth as auth_service


def test_breached_denylist_rejects_password123():
    try:
        assert_password_policy("password123")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_session_limit_revokes_oldest(client, monkeypatch):
    monkeypatch.setenv("MAX_REFRESH_SESSIONS", "2")
    get_settings.cache_clear()
    assert get_settings().max_refresh_sessions == 2

    db = SessionLocal()
    try:
        role = auth_service.get_role(db, "student")
        user = User(
            email="session-limit@example.com",
            password_hash=hash_password("Str0ngPass1!"),
            full_name="SL",
            role=role,
            is_guest=False,
            email_verified_at=utcnow(),
        )
        db.add(user)
        db.flush()
        auth_service.issue_session(db, user, "ua1", "1.1.1.1")
        db.flush()
        auth_service.issue_session(db, user, "ua2", "1.1.1.2")
        db.flush()
        auth_service.issue_session(db, user, "ua3", "1.1.1.3")
        db.commit()
        active = list(
            db.scalars(
                select(SessionToken).where(
                    SessionToken.user_id == user.id,
                    SessionToken.token_type == "refresh",
                    SessionToken.revoked_at.is_(None),
                )
            ).all()
        )
        assert len(active) == 2
    finally:
        db.close()
        get_settings.cache_clear()


def test_lab_idor_assignment_returns_404(client):
    owner = client.post(
        "/api/auth/register",
        json={"email": "lab-owner@example.com", "password": "password12", "full_name": "O"},
    )
    thief = client.post(
        "/api/auth/register",
        json={"email": "lab-thief@example.com", "password": "password12", "full_name": "T"},
    )
    assert owner.status_code == 200 and thief.status_code == 200
    oh = {"Authorization": f"Bearer {owner.json()['access_token']}"}
    th = {"Authorization": f"Bearer {thief.json()['access_token']}"}
    a = client.post("/api/assignments", json={"title": "Secret", "question": "Evaluate X."}, headers=oh)
    assert a.status_code == 200
    assert client.get(f"/api/assignments/{a.json()['id']}", headers=th).status_code == 404


def test_lab_unauthenticated_mutation_denied(client):
    resp = client.post("/api/assignments", json={"title": "x", "question": "Evaluate Y."})
    assert resp.status_code in {401, 403}


def test_lab_alg_none_token_rejected():
    token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001", "typ": "access", "exp": 9999999999},
        key="",
        algorithm="none",
    )
    try:
        decode_token(token)
        ok = False
    except Exception:
        ok = True
    assert ok

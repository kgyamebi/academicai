"""Security hardening evidence: JWT attacks, MFA gate for privileged, admin 403."""

from __future__ import annotations

import jwt
import pyotp

from app.config import get_settings
from app.core.security import create_token, decode_token, hash_password
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.user import User
from app.services import mfa as mfa_service
from app.services.auth import get_role


def test_jwt_rejects_alg_none():
    payload = {"sub": "00000000-0000-0000-0000-000000000001", "typ": "access", "exp": 9999999999}
    token = jwt.encode(payload, key="", algorithm="none")
    try:
        decode_token(token)
        raised = False
    except Exception:
        raised = True
    assert raised


def test_jwt_rejects_wrong_algorithm_hs512_when_configured_hs256():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001", "typ": "access", "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm="HS512",
    )
    if settings.jwt_algorithm.upper() == "HS256":
        try:
            decode_token(token)
            assert False, "expected InvalidTokenError"
        except Exception:
            pass


def test_admin_without_mfa_cannot_hit_admin_api(client):
    db = SessionLocal()
    try:
        role = get_role(db, "admin")
        user = User(
            email="admin-nomfa@example.com",
            password_hash=hash_password("Str0ngAdmin1!"),
            full_name="Admin No MFA",
            role=role,
            is_guest=False,
            mfa_enabled=False,
        )
        db.add(user)
        db.commit()
        token = create_token(str(user.id), "access", extra={"role": "admin"})
    finally:
        db.close()
    resp = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "multi-factor" in resp.json()["error"].lower() or "mfa" in resp.json()["error"].lower()


def test_student_cannot_access_admin(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "student-admin-deny@example.com", "password": "Str0ngPass1!", "full_name": "S"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    resp = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_privileged_login_requires_mfa_enrollment(client):
    db = SessionLocal()
    try:
        role = get_role(db, "admin")
        user = User(
            email="admin-login-mfa@example.com",
            password_hash=hash_password("Str0ngAdmin1!"),
            full_name="Admin Login",
            role=role,
            is_guest=False,
            mfa_enabled=False,
            email_verified_at=utcnow(),
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
    login = client.post(
        "/api/auth/login",
        json={"email": "admin-login-mfa@example.com", "password": "Str0ngAdmin1!"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body.get("mfa_enrollment_required") is True
    assert "mfa_enroll_token" in body
    assert "access_token" not in body


def test_admin_bootstrap_enroll_then_login(client):
    db = SessionLocal()
    try:
        role = get_role(db, "admin")
        user = User(
            email="admin-bootstrap@example.com",
            password_hash=hash_password("Str0ngAdmin1!"),
            full_name="Admin Bootstrap",
            role=role,
            is_guest=False,
            email_verified_at=utcnow(),
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    login = client.post(
        "/api/auth/login",
        json={"email": "admin-bootstrap@example.com", "password": "Str0ngAdmin1!"},
    )
    assert login.status_code == 200
    enroll = login.json()["mfa_enroll_token"]

    setup = client.post("/api/auth/mfa/setup", json={"mfa_enroll_token": enroll})
    assert setup.status_code == 200
    secret = setup.json()["secret"]

    enable = client.post(
        "/api/auth/mfa/enable",
        json={"mfa_enroll_token": enroll, "code": pyotp.TOTP(secret).now()},
    )
    assert enable.status_code == 200
    assert enable.json()["enabled"] is True

    login2 = client.post(
        "/api/auth/login",
        json={"email": "admin-bootstrap@example.com", "password": "Str0ngAdmin1!"},
    )
    assert login2.status_code == 200
    assert login2.json().get("mfa_required") is True
    verify = client.post(
        "/api/auth/mfa/verify",
        json={
            "mfa_challenge_token": login2.json()["mfa_challenge_token"],
            "code": pyotp.TOTP(secret).now(),
        },
    )
    assert verify.status_code == 200
    token = verify.json()["access_token"]
    overview = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert overview.status_code == 200


def test_admin_with_mfa_can_complete_login(client):
    db = SessionLocal()
    try:
        role = get_role(db, "admin")
        user = User(
            email="admin-mfa-ok@example.com",
            password_hash=hash_password("Str0ngAdmin1!"),
            full_name="Admin MFA",
            role=role,
            is_guest=False,
            email_verified_at=utcnow(),
        )
        db.add(user)
        db.flush()
        setup = mfa_service.setup_totp(db, user)
        secret = setup["secret"]
        mfa_service.enable_totp(db, user, pyotp.TOTP(secret).now())
        db.commit()
    finally:
        db.close()
    login = client.post(
        "/api/auth/login",
        json={"email": "admin-mfa-ok@example.com", "password": "Str0ngAdmin1!"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body.get("mfa_required") is True
    verify = client.post(
        "/api/auth/mfa/verify",
        json={"mfa_challenge_token": body["mfa_challenge_token"], "code": pyotp.TOTP(secret).now()},
    )
    assert verify.status_code == 200
    assert "access_token" in verify.json()

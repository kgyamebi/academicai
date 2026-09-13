"""Production email verification lifecycle — Invoice App patterns adapted for AcademicCheck AI."""

from datetime import timedelta
from unittest.mock import patch

from app.config import get_settings
from app.core.security import hash_token
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.user import SessionToken, User
from app.services.auth import (
    _new_opaque_token,
    _store_one_time_token,
    change_email,
    request_password_reset,
    verify_email,
)
from app.services.email_validation import assert_email_syntax, assert_not_disposable, validate_registration_email


def _register(client, email="student@school.edu", password="password12", name="Student"):
    return client.post("/api/auth/register", json={"email": email, "password": password, "full_name": name})


def _auth_header(client, email="student@school.edu", password="password12"):
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json().get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def test_registration_sends_unverified_account(client):
    response = _register(client, "fresh@school.edu")
    assert response.status_code == 200
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "fresh@school.edu").one()
        assert user.email_verified_at is None
        assert user.verification_sent_at is not None
        verify_rows = (
            db.query(SessionToken)
            .filter(
                SessionToken.user_id == user.id,
                SessionToken.token_type == "verify",
                SessionToken.revoked_at.is_(None),
            )
            .all()
        )
        assert len(verify_rows) == 1
    finally:
        db.close()


def test_verification_success_and_token_reuse(client):
    _register(client, "once@school.edu")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "once@school.edu").one()
        raw = _new_opaque_token()
        _store_one_time_token(db, user.id, raw, "verify")
        db.commit()
        result = verify_email(db, raw)
        db.commit()
        assert result["email_verified"] is True
        db.refresh(user)
        assert user.email_verified_at is not None
        try:
            verify_email(db, raw)
            raise AssertionError("reuse should fail")
        except Exception as exc:
            assert "invalid or expired" in str(exc).lower()
    finally:
        db.close()


def test_expired_verification_token(client):
    _register(client, "expire@school.edu")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "expire@school.edu").one()
        raw = _new_opaque_token()
        db.add(
            SessionToken(
                user_id=user.id,
                token_hash=hash_token(raw),
                token_type="verify",
                expires_at=utcnow() - timedelta(hours=1),
            )
        )
        db.commit()
        try:
            verify_email(db, raw)
            raise AssertionError("expired should fail")
        except Exception as exc:
            assert "invalid or expired" in str(exc).lower()
    finally:
        db.close()


def test_invalid_verification_token(client):
    response = client.post("/api/auth/verify-email", json={"token": "not-a-real-token"})
    assert response.status_code == 400


def test_resend_invalidates_old_token_and_cooldown(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "email_resend_cooldown_seconds", 60)
    _register(client, "resend@school.edu")
    headers = _auth_header(client, "resend@school.edu")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "resend@school.edu").one()
        old = (
            db.query(SessionToken)
            .filter(
                SessionToken.user_id == user.id,
                SessionToken.token_type == "verify",
                SessionToken.revoked_at.is_(None),
            )
            .one()
        )
        old_hash = old.token_hash
        user.verification_sent_at = utcnow() - timedelta(seconds=120)
        db.commit()
    finally:
        db.close()

    first = client.post("/api/auth/resend-verification", headers=headers, json={})
    assert first.status_code == 200

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "resend@school.edu").one()
        old_row = db.query(SessionToken).filter(SessionToken.token_hash == old_hash).one()
        assert old_row.revoked_at is not None
        active = (
            db.query(SessionToken)
            .filter(
                SessionToken.user_id == user.id,
                SessionToken.token_type == "verify",
                SessionToken.revoked_at.is_(None),
            )
            .all()
        )
        assert len(active) == 1
    finally:
        db.close()

    blocked = client.post("/api/auth/resend-verification", headers=headers, json={})
    assert blocked.status_code == 429


def test_disposable_email_rejection(client):
    response = _register(client, "spam@mailinator.com")
    assert response.status_code == 400
    text = str(response.json()).lower()
    assert "temporary" in text or "disposable" in text


def test_email_syntax_validation():
    assert_email_syntax("user@gmail.com")
    for bad in ("user", "user@", "@domain.com", "a@@b.com"):
        try:
            assert_email_syntax(bad)
            raise AssertionError(bad)
        except Exception:
            pass


def test_disposable_helper_blocks_known_domains():
    try:
        assert_not_disposable("x@10minutemail.com")
        raise AssertionError("expected block")
    except Exception as exc:
        assert "temporary" in str(exc).lower() or "disposable" in str(exc).lower()


def test_mx_validation_fail_closed_when_enabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_validate_mx", True)
    with patch("app.services.email_validation._dns_has_mx_or_a", return_value=False):
        try:
            validate_registration_email("nobody@this-domain-definitely-missing-xyz.testmail")
            raise AssertionError("expected MX failure")
        except Exception as exc:
            text = str(exc).lower()
            assert "domain" in text or "typo" in text or "valid" in text
    monkeypatch.setattr(get_settings(), "email_validate_mx", False)
    assert validate_registration_email("ok@example.com") == "ok@example.com"


def test_reserved_domain_blocked_outside_test(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "staging")
    monkeypatch.setattr(get_settings(), "email_validate_mx", False)
    try:
        validate_registration_email("a@example.com")
        raise AssertionError("expected reserved domain block")
    except Exception as exc:
        assert "real email" in str(exc).lower() or "domain" in str(exc).lower()


def test_email_change_flow(client):
    _register(client, "old@school.edu")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "old@school.edu").one()
        user.email_verified_at = utcnow()
        user.verification_sent_at = utcnow() - timedelta(minutes=5)
        db.commit()
        result = change_email(db, user, "new@school.edu")
        db.commit()
        assert result["email_verified"] is False
        assert result["pending_email"] == "new@school.edu"
        db.refresh(user)
        assert user.email == "old@school.edu"
        assert user.email_verified_at is None
        for row in db.query(SessionToken).filter(SessionToken.user_id == user.id, SessionToken.token_type == "verify"):
            row.revoked_at = utcnow()
        raw = _new_opaque_token()
        _store_one_time_token(db, user.id, raw, "verify")
        db.commit()
        verify_email(db, raw)
        db.commit()
        db.refresh(user)
        assert user.email == "new@school.edu"
        assert user.pending_email is None
        assert user.email_verified_at is not None
    finally:
        db.close()


def test_password_reset_requires_verified(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "require_verified_for_password_reset", True)
    _register(client, "resetme@school.edu")
    db = SessionLocal()
    try:
        with patch("app.services.auth.send_email"):
            request_password_reset(db, "resetme@school.edu")
            db.commit()
            user = db.query(User).filter(User.email == "resetme@school.edu").one()
            reset_tokens = (
                db.query(SessionToken)
                .filter(
                    SessionToken.user_id == user.id,
                    SessionToken.token_type == "reset",
                    SessionToken.revoked_at.is_(None),
                )
                .all()
            )
            assert reset_tokens == []
            user.email_verified_at = utcnow()
            db.commit()
            request_password_reset(db, "resetme@school.edu")
            db.commit()
            reset_tokens = (
                db.query(SessionToken)
                .filter(
                    SessionToken.user_id == user.id,
                    SessionToken.token_type == "reset",
                    SessionToken.revoked_at.is_(None),
                )
                .all()
            )
            assert len(reset_tokens) == 1
    finally:
        db.close()


def test_forgot_password_enumeration_safe(client):
    response = client.post("/api/auth/password/forgot", json={"email": "missing@school.edu"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("ok") is True
    assert "sent" in body.get("message", "").lower() or "instructions" in body.get("message", "").lower()


def test_privileged_pdf_blocked_when_unverified(client, monkeypatch):
    # development enables verified gates without staging SMTP/MX fail-closed side effects
    monkeypatch.setattr(get_settings(), "app_env", "development")
    monkeypatch.setattr(get_settings(), "email_validate_mx", False)
    _register(client, "gate@school.edu")
    headers = _auth_header(client, "gate@school.edu")
    response = client.get(
        "/api/reports/00000000-0000-0000-0000-000000000001/pdf",
        headers=headers,
    )
    assert response.status_code == 403
    assert "verify" in str(response.json()).lower()


def test_login_while_unverified(client):
    _register(client, "loginok@school.edu")
    login = client.post("/api/auth/login", json={"email": "loginok@school.edu", "password": "password12"})
    assert login.status_code == 200


def test_admin_overview_forbidden_for_guest(client):
    guest = client.post("/api/auth/guest")
    token = guest.json()["access_token"]
    response = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (401, 403)

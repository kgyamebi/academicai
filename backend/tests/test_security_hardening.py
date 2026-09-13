from app.core.security import assert_password_policy, hash_password, verify_password
from app.core.security import create_token
from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import reset_password, verify_email
from app.services.auth import _store_one_time_token
from app.services.emailer import _redact_secrets


def test_new_passwords_use_argon2_when_available():
    hashed = hash_password("password12")
    assert hashed.startswith("$argon2") or hashed.startswith("$2")
    assert verify_password("password12", hashed)
    assert not verify_password("wrong-pass", hashed)


def test_legacy_bcrypt_hashes_still_verify():
    import bcrypt

    legacy = bcrypt.hashpw(b"password12", bcrypt.gensalt()).decode()
    assert verify_password("password12", legacy)
    assert not verify_password("nope", legacy)


def test_password_policy_rejects_common_and_alpha_only():
    try:
        assert_password_policy("12345678")
        raise AssertionError("expected reject")
    except ValueError:
        pass
    try:
        assert_password_policy("abcdefgh")
        raise AssertionError("expected reject")
    except ValueError:
        pass
    assert_password_policy("password12")


def test_register_rejects_common_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "weakpw@example.com", "password": "12345678", "full_name": "W"},
    )
    assert response.status_code == 422


def test_login_allows_unverified_invoice_pattern(client, monkeypatch):
    """Invoice App: login works while unverified; privileged APIs gate separately."""
    from app.config import get_settings

    created = client.post(
        "/api/auth/register",
        json={"email": "needverify@example.com", "password": "password12", "full_name": "V"},
    )
    assert created.status_code == 200
    monkeypatch.setattr(get_settings(), "app_env", "staging")
    allowed = client.post(
        "/api/auth/login",
        json={"email": "needverify@example.com", "password": "password12"},
    )
    assert allowed.status_code == 200
    assert allowed.json().get("access_token") or allowed.cookies.get("ac_access")

def test_reset_token_is_single_use(client):
    client.post(
        "/api/auth/register",
        json={"email": "resetonce@example.com", "password": "password12", "full_name": "R"},
    )
    db = SessionLocal()
    user = db.query(User).filter(User.email == "resetonce@example.com").one()
    token = create_token(str(user.id), "reset")
    _store_one_time_token(db, user.id, token, "reset")
    db.commit()
    reset_password(db, token, "password13")
    db.commit()
    try:
        reset_password(db, token, "password14")
        db.commit()
        raise AssertionError("reset replay should fail")
    except Exception as exc:
        assert "invalid or expired" in str(exc).lower()
    db.close()


def test_verify_token_is_single_use(client):
    client.post(
        "/api/auth/register",
        json={"email": "verifyonce@example.com", "password": "password12", "full_name": "V"},
    )
    db = SessionLocal()
    user = db.query(User).filter(User.email == "verifyonce@example.com").one()
    token = create_token(str(user.id), "verify")
    _store_one_time_token(db, user.id, token, "verify")
    db.commit()
    verify_email(db, token)
    db.commit()
    try:
        verify_email(db, token)
        raise AssertionError("verify replay should fail")
    except Exception as exc:
        assert "invalid or expired" in str(exc).lower()
    db.close()


def test_report_page_size_is_capped(client):
    guest = client.post("/api/auth/guest")
    token = guest.json()["access_token"]
    response = client.get(
        "/api/reports/00000000-0000-0000-0000-000000000001?page_size=100000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_logout_all_revokes_refresh(client):
    created = client.post(
        "/api/auth/register",
        json={"email": "logoutall@example.com", "password": "password12", "full_name": "L"},
    )
    access = created.json()["access_token"]
    refresh = created.json()["refresh_token"]
    gone = client.post("/api/auth/logout-all", headers={"Authorization": f"Bearer {access}"})
    assert gone.status_code == 200
    reused = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert reused.status_code == 401


def test_console_email_redacts_tokens():
    body = "Verify: https://app.example/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aa.bb"
    assert "[REDACTED]" in _redact_secrets(body)
    assert "eyJ" not in _redact_secrets(body)


def test_legacy_bcrypt_marked_for_rehash():
    import bcrypt

    from app.core.security import password_needs_rehash

    legacy = bcrypt.hashpw(b"password12", bcrypt.gensalt()).decode()
    assert password_needs_rehash(legacy) is True
    argon = hash_password("password12")
    if argon.startswith("$argon2"):
        assert password_needs_rehash(argon) is False


def test_admin_flag_schema_rejects_unsafe_keys():
    from pydantic import ValidationError

    from app.schemas.common import AdminFlagIn

    AdminFlagIn(key="coach_v2", enabled=True)
    try:
        AdminFlagIn(key="DROP TABLE users")
        raise AssertionError("expected reject")
    except ValidationError:
        pass


def test_logs_do_not_keep_secret_fields():
    from app.core.logging import _redact_event

    redacted = _redact_event(None, "info", {"password": "password12", "event": "login_failed"})
    assert redacted["password"] == "[REDACTED]"
    assert redacted["event"] == "login_failed"

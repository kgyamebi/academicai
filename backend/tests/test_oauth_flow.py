"""Integration tests for Google/Microsoft OAuth routes and account linking."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import OAuthAccount, User
from app.services.oauth import OAuthProfile, upsert_oauth_user


@pytest.fixture
def google_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-secret")
    monkeypatch.setenv("APP_WEB_URL", "https://academiccheck.org")
    monkeypatch.setenv("APP_API_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("OAUTH_REDIRECT_BASE", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_providers_empty_when_unconfigured(client):
    get_settings.cache_clear()
    res = client.get("/api/auth/oauth/providers")
    assert res.status_code == 200
    assert res.json()["providers"] == []


def test_providers_lists_google(client, google_env):
    res = client.get("/api/auth/oauth/providers")
    assert res.status_code == 200
    assert res.json()["providers"] == ["google"]


def test_oauth_start_redirects_and_sets_state_cookie(client, google_env):
    res = client.get("/api/auth/oauth/google/start?next=/app/dashboard", follow_redirects=False)
    assert res.status_code == 302
    loc = res.headers["location"]
    assert loc.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "client_id=google-client" in loc
    assert "redirect_uri=https%3A%2F%2Facademiccheck.org%2Fapi%2Fauth%2Foauth%2Fgoogle%2Fcallback" in loc
    assert "code_challenge_method=S256" in loc
    assert "ac_oauth_state" in res.cookies


def test_oauth_start_unknown_provider(client, google_env):
    res = client.get("/api/auth/oauth/facebook/start", follow_redirects=False)
    assert res.status_code == 404


def test_upsert_creates_then_reuses_and_links_email(client, google_env):
    db = SessionLocal()
    try:
        profile = OAuthProfile(
            provider="google",
            subject="sub-1",
            email="oauth.user@school.edu",
            email_verified=True,
            full_name="OAuth User",
            raw={"sub": "sub-1"},
        )
        user, created = upsert_oauth_user(db, profile, ip="1.1.1.1")
        db.commit()
        assert created is True
        assert user.email == "oauth.user@school.edu"
        assert user.email_verified_at is not None
        assert user.password_hash is None
        assert db.scalar(select(OAuthAccount).where(OAuthAccount.provider_subject == "sub-1"))

        user2, created2 = upsert_oauth_user(db, profile, ip="1.1.1.1")
        db.commit()
        assert created2 is False
        assert user2.id == user.id
        assert db.scalars(select(OAuthAccount)).all().__len__() == 1

        # Existing password account with same email gets linked
        other = User(
            email="linked@school.edu",
            password_hash=hash_password("Password123!"),
            full_name="Existing",
            is_guest=False,
            is_active=True,
        )
        db.add(other)
        db.commit()
        link_profile = OAuthProfile(
            provider="microsoft",
            subject="ms-22",
            email="linked@school.edu",
            email_verified=True,
            full_name="Existing",
            raw={"id": "ms-22"},
        )
        linked, created3 = upsert_oauth_user(db, link_profile)
        db.commit()
        assert created3 is False
        assert linked.id == other.id
        assert linked.password_hash is not None
        assert db.scalar(
            select(OAuthAccount).where(OAuthAccount.provider == "microsoft", OAuthAccount.provider_subject == "ms-22")
        )
    finally:
        db.close()


def test_oauth_callback_success_sets_session(client, google_env):
    start = client.get("/api/auth/oauth/google/start?next=/app/dashboard", follow_redirects=False)
    state = start.cookies.get("ac_oauth_state")
    assert state

    fake_profile = OAuthProfile(
        provider="google",
        subject="cb-sub",
        email="callback@school.edu",
        email_verified=True,
        full_name="Callback User",
        raw={"sub": "cb-sub"},
    )

    with patch("app.services.oauth.exchange_code", return_value=fake_profile):
        res = client.get(
            f"/api/auth/oauth/google/callback?code=fake-code&state={state}",
            follow_redirects=False,
        )
    assert res.status_code == 302
    assert res.headers["location"].endswith("/onboarding?signup=1")
    assert "ac_access" in res.cookies
    assert "ac_refresh" in res.cookies

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "callback@school.edu"
    assert body["email_verified"] is True


def test_oauth_callback_rejects_state_mismatch(client, google_env):
    client.get("/api/auth/oauth/google/start", follow_redirects=False)
    res = client.get(
        "/api/auth/oauth/google/callback?code=x&state=not-the-cookie-state",
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "login?" in res.headers["location"]
    assert "error=" in res.headers["location"]


def test_redirect_uri_uses_public_web_when_api_is_loopback(google_env):
    from app.services import oauth as oauth_service

    assert oauth_service.redirect_uri("google") == "https://academiccheck.org/api/auth/oauth/google/callback"

"""Unit tests for OAuth helpers (no live IdP calls)."""

from app.services.oauth import _normalize_profile, _safe_next


def test_safe_next_blocks_open_redirect():
    assert _safe_next("/app/dashboard") == "/app/dashboard"
    assert _safe_next("//evil.com") == "/app/dashboard"
    assert _safe_next("https://evil.com") == "/app/dashboard"
    assert _safe_next("/onboarding") == "/onboarding"


def test_normalize_google_profile():
    profile = _normalize_profile(
        "google",
        {"sub": "g-123", "email": "Student@Gmail.com", "email_verified": True, "name": "Ada"},
    )
    assert profile.provider == "google"
    assert profile.subject == "g-123"
    assert profile.email == "student@gmail.com"
    assert profile.email_verified is True
    assert profile.full_name == "Ada"


def test_normalize_microsoft_profile():
    profile = _normalize_profile(
        "microsoft",
        {"id": "ms-9", "mail": None, "userPrincipalName": "student@contoso.edu", "displayName": "Ada"},
    )
    assert profile.subject == "ms-9"
    assert profile.email == "student@contoso.edu"
    assert profile.full_name == "Ada"

"""New adversarial coverage beyond the 6 lab attacks."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.rate_limit import LIMITS, _hits, check_rate_limit
from app.services.documents.validation import DocumentSecurityError, _ext


def _register(client, email: str) -> dict:
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": "password12", "full_name": "Adv"},
    ).json()


def test_mass_assignment_rejected_on_register(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "mass@example.com",
            "password": "password12",
            "full_name": "M",
            "is_admin": True,
            "role": "admin",
            "credits": 9999,
        },
    )
    assert response.status_code == 422


def test_mass_assignment_rejected_on_assignment_create(client):
    token = _register(client, "mass-asg@example.com")["access_token"]
    response = client.post(
        "/api/assignments",
        json={"title": "T", "question": "Evaluate trade policy in detail.", "user_id": "not-mine", "status": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_http_parameter_pollution_does_not_override_owner(client):
    owner = _register(client, "hpp-owner@example.com")
    thief = _register(client, "hpp-thief@example.com")
    created = client.post(
        "/api/assignments",
        json={"title": "Secret", "question": "Evaluate X thoroughly."},
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    aid = created.json()["id"]
    polluted = client.get(
        f"/api/assignments/{aid}?user_id={thief['user']['id']}&user_id={owner['user']['id']}",
        headers={"Authorization": f"Bearer {thief['access_token']}"},
    )
    assert polluted.status_code == 404


def test_graphql_introspection_not_exposed(client):
    assert client.get("/graphql").status_code == 404
    assert client.get("/api/graphql").status_code == 404
    assert client.post("/graphql", json={"query": "{__schema{types{name}}}"}).status_code == 404


def test_csrf_blocks_cookie_mutating_request(client):
    client.post(
        "/api/auth/register",
        json={"email": "csrf-adv@example.com", "password": "password12", "full_name": "C"},
    )
    # Cookies are stored; omit Authorization so CSRF applies.
    response = client.post("/api/assignments", json={"title": "CSRF", "question": "Evaluate something substantial."})
    assert response.status_code == 403


def test_clickjacking_headers_deny_framing(client):
    response = client.get("/api/live")
    assert response.headers.get("X-Frame-Options") == "DENY"
    csp = response.headers.get("Content-Security-Policy") or ""
    assert "frame-ancestors 'none'" in csp


def test_rate_limit_ignores_x_forwarded_for(monkeypatch):
    from types import SimpleNamespace

    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "app_env", "development")
    _hits.clear()
    client = SimpleNamespace(host="10.0.0.9")
    limit = LIMITS["guest"]["login"]
    last_status = None
    for i in range(limit + 2):
        req = SimpleNamespace(client=client, headers={"x-forwarded-for": f"8.8.8.{i}", "x-real-ip": f"9.9.9.{i}"})
        try:
            check_rate_limit(req, "login", user=None)
            last_status = 200
        except Exception as exc:  # noqa: BLE001
            last_status = getattr(exc, "status_code", 500)
    assert last_status == 429


@settings(max_examples=40, deadline=None)
@given(st.text(min_size=1, max_size=40))
def test_hypothesis_filename_never_accepts_null_or_slash(name: str):
    if "\x00" in name or "/" in name.replace("\\", "/") or name.startswith("."):
        try:
            _ext(name)
            raise AssertionError("expected reject")
        except DocumentSecurityError:
            return
    # Names without a real extension still reject.
    if "." not in name.strip():
        try:
            _ext(name)
            raise AssertionError("expected reject")
        except DocumentSecurityError:
            return

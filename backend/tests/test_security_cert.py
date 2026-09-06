def test_security_headers_present(client):
    response = client.get("/api/live")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin" in (response.headers.get("Referrer-Policy") or "")


def test_readiness_reports_database(client):
    response = client.get("/api/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] is True
    assert "ready" in body


def test_lockout_after_repeated_failures(client):
    client.post(
        "/api/auth/register",
        json={"email": "lockme@example.com", "password": "password12", "full_name": "Lock"},
    )
    last = None
    for _ in range(8):
        last = client.post("/api/auth/login", json={"email": "lockme@example.com", "password": "wrong-pass"})
    assert last.status_code in {401, 403}
    locked = client.post("/api/auth/login", json={"email": "lockme@example.com", "password": "password12"})
    assert locked.status_code == 403


def test_refresh_reuse_is_rejected(client):
    created = client.post(
        "/api/auth/register",
        json={"email": "reuse@example.com", "password": "password12", "full_name": "Reuse"},
    )
    refresh = created.json()["refresh_token"]
    first = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert first.status_code == 200
    second = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert second.status_code == 401

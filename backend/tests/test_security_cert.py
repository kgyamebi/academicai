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
    rotated = first.json()["refresh_token"]
    second = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert second.status_code == 401
    family = client.post("/api/auth/refresh", json={"refresh_token": rotated})
    assert family.status_code == 401


def test_login_stores_device_ip_and_user_agent(client):
    client.post(
        "/api/auth/register",
        json={"email": "device-track@example.com", "password": "password12", "full_name": "Device"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "device-track@example.com", "password": "password12"},
        headers={"User-Agent": "AcademicCheck-Cert/1.0"},
    )
    assert login.status_code == 200
    from app.db.session import SessionLocal
    from app.models.user import SessionToken, User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "device-track@example.com").one()
        row = (
            db.query(SessionToken)
            .filter(SessionToken.user_id == user.id, SessionToken.token_type == "refresh")
            .order_by(SessionToken.created_at.desc())
            .first()
        )
        assert row is not None
        assert row.user_agent == "AcademicCheck-Cert/1.0"
        assert row.ip_address
    finally:
        db.close()

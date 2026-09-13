from pathlib import Path


def test_pdf_download_eager_loads_scores():
    text = Path(__file__).resolve().parents[1].joinpath("app/api/v1/reports.py").read_text(encoding="utf-8")
    download = text.split("def download_pdf", 1)[1].split("def create_share", 1)[0]
    assert "selectinload(AnalysisReport.scores)" in download
    assert "db.get(AnalysisReport, report_id)" not in download
    assert "def _owned_report" in text
    shared = text.split("def _shared_report", 1)[1].split("def _audit", 1)[0]
    assert "selectinload(AnalysisReport.scores)" in shared


def test_public_lists_are_capped():
    text = Path(__file__).resolve().parents[1].joinpath("app/api/v1/public.py").read_text(encoding="utf-8")
    assert ".limit(50)" in text
    assert ".limit(100)" in text


def test_http_errors_are_structured(client):
    response = client.get("/api/assignments/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 401
    body = response.json()
    assert body["error"]
    assert body["status"] == 401
    assert "traceback" not in body
    assert "Traceback" not in response.text


def test_validation_errors_do_not_echo_internals(client):
    response = client.post("/api/auth/login", json={"email": "not-an-email"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Please check the submitted information."
    assert "loc" not in body


def test_queue_helpers_log_unavailable_backends():
    text = Path(__file__).resolve().parents[1].joinpath("app/workers/queue.py").read_text(encoding="utf-8")
    assert "worker_count_unavailable" in text
    assert "queue_depth_unavailable" in text
    assert "terminal_job_lookup_failed" in text


def test_openapi_lists_core_contract_paths(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in (
        "/api/live",
        "/api/ready",
        "/api/auth/login",
        "/api/assignments",
        "/api/reports/{report_id}",
        "/api/billing/webhooks/stripe",
        "/api/citations",
        "/api/citations/verify",
    ):
        assert path in paths


def test_citation_rate_limit_bucket_exists():
    from app.core.rate_limit import LIMITS

    for role in LIMITS:
        assert "citation" in LIMITS[role] or "default" in LIMITS[role]


def test_account_delete_cancels_subscription_and_blocks_login(client):
    created = client.post(
        "/api/auth/register",
        json={"email": "gone-audit@example.com", "password": "password12", "full_name": "Gone"},
    )
    assert created.status_code == 200
    token = created.json()["access_token"]
    deleted = client.delete("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert deleted.status_code == 200
    login = client.post(
        "/api/auth/login",
        json={"email": "gone-audit@example.com", "password": "password12"},
    )
    assert login.status_code in {401, 403}

    from app.db.session import SessionLocal
    from app.models.billing import Subscription
    from app.models.user import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.full_name == "Deleted user").order_by(User.created_at.desc()).first()
        assert user is not None
        assert user.is_active is False
        subs = db.query(Subscription).filter(Subscription.user_id == user.id).all()
        assert subs
        assert all(s.status == "cancelled" for s in subs)
    finally:
        db.close()


def test_expired_guest_documents_are_purged(client):
    from datetime import timedelta
    from uuid import UUID

    from app.core.time import utcnow
    from app.db.session import SessionLocal
    from app.models.document import Document
    from app.services.analysis.runner import purge_expired_guest_documents

    guest = client.post("/api/auth/guest")
    headers = {"Authorization": f"Bearer {guest.json()['access_token']}"}
    assignment = client.post(
        "/api/assignments",
        json={"title": "Guest draft", "question": "Compare and evaluate globalization."},
        headers=headers,
    )
    document = client.post(
        "/api/documents/paste",
        json={
            "assignment_id": assignment.json()["id"],
            "text": "Globalization effects " * 40,
            "filename": "draft.txt",
        },
        headers=headers,
    )
    doc_id = UUID(document.json()["id"])
    db = SessionLocal()
    try:
        row = db.get(Document, doc_id)
        assert row is not None
        row.expires_at = utcnow() - timedelta(hours=1)
        db.commit()
        purged = purge_expired_guest_documents(db)
        db.commit()
        row = db.get(Document, doc_id)
        assert purged >= 1
        assert row.deleted_at is not None
        assert row.extracted_text == ""
    finally:
        db.close()

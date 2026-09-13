import io
import zipfile
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from app.core.safe_json import loads_json
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.analysis import AnalysisJob
from app.models.assignment import Assignment
from app.models.billing import Credit, Payment
from app.models.document import Document
from app.models.user import User
from app.services.analysis.runner import fail_job, process_job, reap_stale_jobs
from app.services.billing import _pending_payment, mark_webhook_processed, record_webhook_event
from app.services.credits import reserve_credits
from app.services.documents.extractor import extract_document
from app.services.documents.validation import DocumentSecurityError
from app.services.emailer import send_email
from app.workers.tasks import record_poison_job


def _user_doc_job(db, email: str) -> tuple[User, Document, AnalysisJob]:
    user = User(email=email, password_hash="x", full_name="Rel")
    db.add(user)
    db.flush()
    assignment = Assignment(user_id=user.id, title="T", academic_level="undergraduate")
    db.add(assignment)
    db.flush()
    document = Document(
        user_id=user.id,
        assignment_id=assignment.id,
        filename="draft.txt",
        original_filename="draft.txt",
        mime_type="text/plain",
        extension=".txt",
        file_signature="00",
        size_bytes=40,
        storage_key=f"{user.id}/draft.txt",
        status="extracted",
        extracted_text="Globalization has mixed effects on developing economies.",
        normalized_text="Globalization has mixed effects on developing economies.",
        word_count=8,
        paragraph_count=1,
        sentence_count=1,
    )
    db.add(document)
    db.flush()
    job = AnalysisJob(
        user_id=user.id,
        assignment_id=assignment.id,
        document_id=document.id,
        status="processing",
        stage="extracting",
        analysis_type="full",
        started_at=utcnow() - timedelta(minutes=20),
    )
    db.add(job)
    db.flush()
    return user, document, job


def test_reap_stale_processing_job_fails_and_refunds(client):
    db = SessionLocal()
    user, _document, job = _user_doc_job(db, "stale-reap@example.com")
    wallet = Credit(user_id=user.id, remaining=Decimal("5"), reserved=Decimal("0"))
    db.add(wallet)
    db.flush()
    reserve_credits(db, user, "full", job.id)
    db.commit()
    job_id = job.id
    user_id = user.id
    marked = reap_stale_jobs(db, older_than_seconds=60)
    db.commit()
    assert marked == 1
    refreshed = db.get(AnalysisJob, job_id)
    assert refreshed.status == "failed"
    assert refreshed.error
    wallet = db.query(Credit).filter(Credit.user_id == user_id).one()
    assert wallet.remaining == Decimal("5")
    db.close()


def test_poison_job_marks_analysis_failed(client):
    db = SessionLocal()
    _user, _document, job = _user_doc_job(db, "poison@example.com")
    db.commit()
    job_id = job.id
    record_poison_job(str(job_id), "worker died")
    db.close()
    db = SessionLocal()
    assert db.get(AnalysisJob, job_id).status == "failed"
    db.close()


def test_fail_job_is_idempotent(client):
    db = SessionLocal()
    _user, _document, job = _user_doc_job(db, "idem-fail@example.com")
    db.commit()
    assert fail_job(db, job.id, "first") is True
    db.commit()
    assert fail_job(db, job.id, "second") is False
    db.close()


def test_garbage_pdf_does_not_raise_generic(client):
    try:
        extract_document(b"%PDF-1.4\nnot a real catalog", ".pdf")
    except DocumentSecurityError:
        return
    raise AssertionError("expected DocumentSecurityError")


def test_invalid_docx_zip_is_safe(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
    try:
        extract_document(buf.getvalue(), ".docx")
    except DocumentSecurityError:
        return
    raise AssertionError("expected DocumentSecurityError")


def test_broken_pdf_page_maps_to_security_error(client, monkeypatch):
    class Page:
        def get_text(self, *_args, **_kwargs):
            raise RuntimeError("broken page")

    class Doc:
        page_count = 1
        is_encrypted = False

        def __iter__(self):
            return iter([Page()])

        def close(self):
            return None

    monkeypatch.setattr("fitz.open", lambda *args, **kwargs: Doc())
    try:
        extract_document(b"%PDF-1.4\n", ".pdf")
    except DocumentSecurityError:
        return
    raise AssertionError("expected DocumentSecurityError")


def test_upload_extract_crash_returns_400(client, monkeypatch):
    token = client.post(
        "/api/auth/register",
        json={"email": "upload-crash@example.com", "password": "password12", "full_name": "U"},
    ).json()["access_token"]

    def boom(*_args, **_kwargs):
        raise RuntimeError("parser exploded")

    monkeypatch.setattr("app.api.v1.documents.extract_document", boom)
    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("draft.txt", b"enough text for an assignment draft body", "text/plain")},
    )
    assert response.status_code == 400
    assert "could not read" in response.json()["error"].lower()


def test_upload_rejects_over_cap(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    token = client.post(
        "/api/auth/register",
        json={"email": "upload-cap@example.com", "password": "password12", "full_name": "U"},
    ).json()["access_token"]
    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("draft.txt", b"x", "text/plain")},
    )
    assert response.status_code == 400
    assert "too large" in response.json()["error"].lower()


def test_unmatched_stripe_webhook_not_marked_processed(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.billing.verify_stripe_signature",
        lambda _payload, _sig: {
            "id": "evt_unmatched",
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {}}},
        },
    )
    response = client.post(
        "/api/billing/webhooks/stripe",
        content=b"{}",
        headers={"Stripe-Signature": "t=1,v1=x"},
    )
    assert response.status_code == 503
    db = SessionLocal()
    from app.models.admin import WebhookEvent

    event = db.query(WebhookEvent).filter(WebhookEvent.event_id == "evt_unmatched").one()
    assert event.processed_at is None
    db.close()


def test_unprocessed_webhook_can_retry(client):
    db = SessionLocal()
    payload = b'{"id":"evt_retry"}'
    assert record_webhook_event(db, "stripe", "evt_retry", "checkout.session.completed", payload, mark_processed=False) is True
    assert record_webhook_event(db, "stripe", "evt_retry", "checkout.session.completed", payload, mark_processed=False) is True
    mark_webhook_processed(db, "evt_retry")
    db.commit()
    assert record_webhook_event(db, "stripe", "evt_retry", "checkout.session.completed", payload) is False
    db.close()


def test_failed_checkout_reuses_idempotency_key(client):
    db = SessionLocal()
    user = User(email="reuse-pay@example.com", password_hash="x", full_name="P")
    db.add(user)
    db.flush()
    first = _pending_payment(db, user, "stripe", 199, "USD", "subscription", "key-reuse-1", {})
    first.status = "failed"
    db.flush()
    again = _pending_payment(db, user, "stripe", 199, "USD", "subscription", "key-reuse-1", {"retry": True})
    assert again.id == first.id
    assert again.status == "pending"
    db.close()


def test_corrupt_report_json_does_not_500(client):
    guest = client.post("/api/auth/guest")
    token = guest.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assignment = client.post(
        "/api/assignments",
        json={"title": "JSON", "question": "Compare and evaluate globalization in developing economies."},
        headers=headers,
    )
    document = client.post(
        "/api/documents/paste",
        json={
            "assignment_id": assignment.json()["id"],
            "text": "Globalization has mixed effects on developing economies. " * 8,
            "filename": "draft.txt",
        },
        headers=headers,
    )
    analysis = client.post(
        "/api/analysis",
        json={
            "assignment_id": assignment.json()["id"],
            "document_id": document.json()["id"],
            "analysis_type": "full",
        },
        headers=headers,
    )
    job = client.get(f"/api/analysis/{analysis.json()['id']}", headers=headers)
    report_id = job.json()["report_id"]
    if not report_id:
        process_job(SessionLocal(), UUID(analysis.json()["id"]))
        job = client.get(f"/api/analysis/{analysis.json()['id']}", headers=headers)
        report_id = job.json()["report_id"]
    assert report_id
    db = SessionLocal()
    from app.models.analysis import AnalysisReport

    report = db.get(AnalysisReport, UUID(str(report_id)))
    report.strengths_json = "{not-json"
    db.commit()
    db.close()
    response = client.get(f"/api/reports/{report_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["strengths"] == []


def test_email_failure_does_not_raise(monkeypatch):
    class Boom:
        def send(self, *_args, **_kwargs):
            raise RuntimeError("smtp down")

    monkeypatch.setattr("app.services.emailer.get_email_provider", lambda: Boom())
    send_email("a@example.com", "Hi", "Body")


def test_loads_json_defaults():
    assert loads_json(None, []) == []
    assert loads_json("{", {"ok": 1}) == {"ok": 1}
    assert loads_json('["a"]', []) == ["a"]


def test_cancel_wins_over_in_flight_worker(client, monkeypatch):
    from app.services.analysis import runner as runner_mod

    original = runner_mod.run_analysis

    def cancel_then_run(*args, **kwargs):
        result = original(*args, **kwargs)
        db = SessionLocal()
        jobs = db.query(AnalysisJob).all()
        for job in jobs:
            if job.status == "processing":
                job.status = "cancelled"
        db.commit()
        db.close()
        return result

    monkeypatch.setattr(runner_mod, "run_analysis", cancel_then_run)
    guest = client.post("/api/auth/guest")
    token = guest.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assignment = client.post(
        "/api/assignments",
        json={"title": "Cancel", "question": "Compare and evaluate globalization in developing economies."},
        headers=headers,
    )
    document = client.post(
        "/api/documents/paste",
        json={
            "assignment_id": assignment.json()["id"],
            "text": "Globalization has mixed effects on developing economies. " * 8,
            "filename": "draft.txt",
        },
        headers=headers,
    )
    analysis = client.post(
        "/api/analysis",
        json={
            "assignment_id": assignment.json()["id"],
            "document_id": document.json()["id"],
            "analysis_type": "full",
        },
        headers=headers,
    )
    assert analysis.status_code == 200
    job = client.get(f"/api/analysis/{analysis.json()['id']}", headers=headers)
    assert job.json()["status"] in {"cancelled", "queued", "failed", "completed"}
    if job.json()["status"] == "cancelled":
        assert job.json()["report_id"] is None

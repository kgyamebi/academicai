"""Scale pass: deep OFFSET closed at the API, PDF/DOCX off the request thread, CDN headers."""

from __future__ import annotations

import io
import time
from uuid import uuid4

import fitz
from docx import Document as DocxDocument

from app.core.pagination import DEEP_OFFSET_MESSAGE, MAX_OFFSET_ROWS
from app.services.documents.extractor import extract_document


def _token(client, email: str) -> dict:
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password12", "full_name": "Scale"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Globalization has mixed effects on developing economies. " * 20)
    blob = doc.tobytes()
    doc.close()
    return blob


def _docx_bytes() -> bytes:
    doc = DocxDocument()
    doc.add_paragraph("Globalization has mixed effects on developing economies because institutions differ.")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_deep_assignment_offset_is_rejected_without_slow_scan(client):
    headers = _token(client, f"offset-{uuid4().hex[:10]}@example.com")
    page = (MAX_OFFSET_ROWS // 20) + 2
    started = time.perf_counter()
    response = client.get("/api/assignments", params={"page": page, "page_size": 20}, headers=headers)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert response.status_code == 400, response.text
    assert "cursor-based pagination" in response.json()["error"].lower()
    assert elapsed_ms < 500
    shallow = client.get("/api/assignments", params={"page": 2, "page_size": 20}, headers=headers)
    assert shallow.status_code == 200


def test_deep_findings_offset_is_rejected(client):
    headers = _token(client, f"findings-off-{uuid4().hex[:10]}@example.com")
    page = (MAX_OFFSET_ROWS // 40) + 2
    response = client.get(
        "/api/reports/00000000-0000-0000-0000-000000000001",
        params={"page": page, "page_size": 40},
        headers=headers,
    )
    assert response.status_code in {400, 404}
    if response.status_code == 400:
        assert "cursor" in response.json()["error"].lower()


def test_pdf_upload_returns_before_extract_when_queue_accepts(client, monkeypatch):
    called = {"n": 0}
    real = extract_document

    def wrapped(*args, **kwargs):
        called["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr("app.api.v1.documents.enqueue_extract", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("app.api.v1.documents.extract_document", wrapped)
    monkeypatch.setattr("app.services.documents.extract_job.extract_document", wrapped)
    headers = _token(client, f"pdfq-{uuid4().hex[:10]}@example.com")
    started = time.perf_counter()
    response = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("essay.pdf", _pdf_bytes(), "application/pdf")},
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert called["n"] == 0
    assert elapsed_ms < 5000


def test_analysis_waits_until_document_extracted(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.documents.enqueue_extract", lambda *_args, **_kwargs: True)
    headers = _token(client, f"wait-{uuid4().hex[:10]}@example.com")
    assignment = client.post(
        "/api/assignments",
        json={"title": "T", "question": "Evaluate globalization in developing economies."},
        headers=headers,
    )
    assert assignment.status_code == 200
    uploaded = client.post(
        "/api/documents/upload",
        headers=headers,
        data={"assignment_id": assignment.json()["id"]},
        files={"file": ("essay.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["status"] == "queued"
    analysis = client.post(
        "/api/analysis",
        json={
            "assignment_id": assignment.json()["id"],
            "document_id": uploaded.json()["id"],
            "analysis_type": "full",
        },
        headers=headers,
    )
    assert analysis.status_code == 409


def test_extract_job_completes_queued_pdf(client, monkeypatch):
    from app.services.documents.extract_job import process_extract_job

    monkeypatch.setattr("app.api.v1.documents.enqueue_extract", lambda *_args, **_kwargs: True)
    headers = _token(client, f"exjob-{uuid4().hex[:10]}@example.com")
    uploaded = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("essay.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert uploaded.json()["status"] == "queued"
    process_extract_job(uploaded.json()["id"])
    got = client.get(f"/api/documents/{uploaded.json()['id']}", headers=headers)
    assert got.status_code == 200
    assert got.json()["status"] == "extracted"
    assert got.json()["word_count"] > 0


def test_public_get_sends_cdn_cache_headers(client):
    response = client.get("/api/public/faqs")
    assert response.status_code == 200
    cache = response.headers.get("cache-control", "")
    assert "public" in cache
    assert "max-age=60" in cache
    assert response.headers.get("surrogate-key") == "public-meta"
    assert response.headers.get("cdn-cache-control", "").startswith("public")


def test_tenant_lists_remain_no_store(client):
    headers = _token(client, f"nostore-{uuid4().hex[:10]}@example.com")
    response = client.get("/api/assignments", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
    assert response.headers.get("cdn-cache-control") == "no-store"


def test_docx_upload_is_queued_not_inline(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.documents.enqueue_extract", lambda *_args, **_kwargs: True)
    headers = _token(client, f"docx-{uuid4().hex[:10]}@example.com")
    response = client.post(
        "/api/documents/upload",
        headers=headers,
        files={
            "file": (
                "essay.docx",
                _docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "queued"


def test_deep_offset_message_is_explicit():
    assert "cursor-based" in DEEP_OFFSET_MESSAGE.lower()
    assert MAX_OFFSET_ROWS == 200

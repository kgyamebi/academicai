"""MFA TOTP + worker orphan recovery — executed tests."""

from __future__ import annotations

from datetime import timedelta

import pyotp
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.analysis import AnalysisJob
from app.models.assignment import Assignment
from app.models.document import Document
from app.models.user import User
from app.services import auth as auth_service
from app.services import mfa as mfa_service
from app.services.analysis.runner import recover_orphaned_jobs


def test_totp_setup_enable_login_challenge(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "mfa-user@example.com", "password": "Str0ngPass1!", "full_name": "MFA User"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    setup = client.post("/api/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    code = pyotp.TOTP(secret).now()
    enable = client.post("/api/auth/mfa/enable", json={"code": code}, headers=headers)
    assert enable.status_code == 200
    assert enable.json()["enabled"] is True
    assert len(enable.json()["backup_codes"]) == 8

    client.post("/api/auth/logout", headers=headers)
    login = client.post("/api/auth/login", json={"email": "mfa-user@example.com", "password": "Str0ngPass1!"})
    assert login.status_code == 200
    body = login.json()
    assert body.get("mfa_required") is True
    assert "mfa_challenge_token" in body
    assert "access_token" not in body

    verify = client.post(
        "/api/auth/mfa/verify",
        json={"mfa_challenge_token": body["mfa_challenge_token"], "code": pyotp.TOTP(secret).now()},
    )
    assert verify.status_code == 200
    assert "access_token" in verify.json()


def test_recover_orphaned_job_exactly_once(client):
    # client fixture creates schema
    db: Session = SessionLocal()
    try:
        user = User(email="orphan@example.com", password_hash="x", full_name="O", is_guest=False)
        db.add(user)
        db.flush()
        assignment = Assignment(user_id=user.id, title="t", academic_level="undergraduate")
        db.add(assignment)
        db.flush()
        document = Document(
            user_id=user.id,
            assignment_id=assignment.id,
            filename="a.txt",
            original_filename="a.txt",
            mime_type="text/plain",
            extension=".txt",
            storage_key=f"{user.id}/a.txt",
            extracted_text="hello",
            normalized_text="hello",
            word_count=1,
            status="extracted",
        )
        db.add(document)
        db.flush()
        job = AnalysisJob(
            user_id=user.id,
            assignment_id=assignment.id,
            document_id=document.id,
            status="processing",
            stage="checking_citations",
            started_at=utcnow() - timedelta(minutes=5),
            heartbeat_at=utcnow() - timedelta(minutes=5),
            recovery_count=0,
        )
        db.add(job)
        db.commit()
        job_id = job.id

        first = recover_orphaned_jobs(db, older_than_seconds=60)
        db.commit()
        assert first == [job_id]
        refreshed = db.get(AnalysisJob, job_id)
        assert refreshed.status == "queued"
        assert refreshed.recovery_count == 1

        # Simulate second crash after requeue pickup
        refreshed.status = "processing"
        refreshed.started_at = utcnow() - timedelta(minutes=5)
        refreshed.heartbeat_at = utcnow() - timedelta(minutes=5)
        db.commit()
        second = recover_orphaned_jobs(db, older_than_seconds=60)
        db.commit()
        assert second == []
        final = db.get(AnalysisJob, job_id)
        assert final.status == "failed"
        assert "could not be recovered" in (final.error or "")
    finally:
        db.close()


def test_secret_literal_scan_includes_common_patterns():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    forbidden = (
        b"sk_live_",
        b"whsec_",
        b"AKIA",
        b"BEGIN RSA PRIVATE KEY",
        b"-----BEGIN PRIVATE KEY-----",
        b"xoxb-",
        b"ghp_",
    )
    for path in root.rglob("*.py"):
        if path.name in {"firewall.py", "logging.py"}:
            continue
        data = path.read_bytes()
        for needle in forbidden:
            assert needle not in data, f"{path} contains {needle!r}"
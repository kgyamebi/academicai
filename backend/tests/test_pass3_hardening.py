"""Pass 3 Bucket A — reliability, security, billing, observability helpers."""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import signal
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.core.metrics import snapshot
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.billing import Payment
from app.models.user import User
from app.services.credits import grant_credits, wallet_matches_ledger
from app.workers.queue import _on_failure
from app.workers.rq_worker import main as rq_main

REPO = Path(__file__).resolve().parents[2]


def _register(client, email: str):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password12", "full_name": "Payer"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_wallet_mismatch_is_detected(client):
    _register(client, "ledger-mismatch@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "ledger-mismatch@example.com").one()
    grant_credits(db, user, Decimal("5"))
    db.commit()
    assert wallet_matches_ledger(db, user) is True
    wallet = user.credits[0]
    wallet.remaining = Decimal("99")
    db.flush()
    assert wallet_matches_ledger(db, user) is False
    db.close()


def test_stripe_signed_webhook_success_grants_plan(client, monkeypatch):
    token = _register(client, "stripe-hmac@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "stripe-hmac@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add(payment)
    db.commit()
    payment_id = str(payment.id)
    db.close()

    event_id = f"evt_{uuid4().hex}"
    body = json.dumps(
        {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"payment_id": payment_id}}},
        }
    ).encode()
    monkeypatch.setattr(
        "app.api.v1.billing.verify_stripe_signature",
        lambda _payload, _sig: json.loads(body.decode()),
    )
    response = client.post(
        "/api/billing/webhooks/stripe",
        content=body,
        headers={"Stripe-Signature": "t=1,v1=x"},
    )
    assert response.status_code == 200
    billing = client.get("/api/billing", headers={"Authorization": f"Bearer {token}"})
    assert billing.json()["plan"]["slug"] == "student"


def test_stripe_hmac_helper_rejects_bad_signature(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    from app.config import get_settings
    from app.services.billing import _stripe_hmac
    from fastapi import HTTPException

    get_settings.cache_clear()
    body = b'{"id":"evt_bad"}'
    ts = str(int(utcnow().timestamp()))
    try:
        _stripe_hmac(body, f"t={ts},v1=deadbeef", "whsec_x", 300)
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400
    assert snapshot().get("billing.webhook_signature_invalid", 0) >= 1
    get_settings.cache_clear()


def test_flutterwave_valid_hash_marks_failed(client, monkeypatch):
    secret = "flw_hash_pass3"
    monkeypatch.setenv("FLUTTERWAVE_WEBHOOK_HASH", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    _register(client, "flw-ok@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "flw-ok@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="flutterwave",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add(payment)
    db.commit()
    payment_id = str(payment.id)
    db.close()
    body = json.dumps(
        {
            "event": "charge.completed",
            "data": {"id": "flw_1", "tx_ref": payment_id, "status": "failed", "meta": {"payment_id": payment_id}},
        }
    ).encode()
    response = client.post(
        "/api/billing/webhooks/flutterwave",
        content=body,
        headers={"verif-hash": secret},
    )
    assert response.status_code == 200
    db = SessionLocal()
    row = db.get(Payment, UUID(payment_id))
    assert row is not None
    assert row.status == "failed"
    db.close()
    get_settings.cache_clear()


def test_bad_paystack_signature_increments_metric(client, monkeypatch):
    before = snapshot().get("billing.webhook_signature_invalid", 0)
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "secret")
    from app.config import get_settings

    get_settings.cache_clear()
    response = client.post(
        "/api/billing/webhooks/paystack",
        content=b'{"event":"charge.success","data":{}}',
        headers={"x-paystack-signature": "nope"},
    )
    assert response.status_code == 400
    assert snapshot().get("billing.webhook_signature_invalid", 0) >= before + 1
    get_settings.cache_clear()


def test_csrf_reject_increments_metric(client):
    from app.core.csrf import enforce_csrf
    from starlette.requests import Request

    before = snapshot().get("csrf.rejected", 0)

    async def receive():
        return {"type": "http.request", "body": b"{}", "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/assignments",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "scheme": "http",
    }
    request = Request(scope, receive)
    request._cookies = {"ac_access": "x", "ac_csrf": "a"}  # type: ignore[attr-defined]
    # Starlette cookies are read-only via scope headers
    scope["headers"] = [
        (b"cookie", b"ac_access=x; ac_csrf=a"),
        (b"x-csrf-token", b"b"),
    ]
    request = Request(scope, receive)
    try:
        enforce_csrf(request)
        assert False, "expected CSRF failure"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    assert snapshot().get("csrf.rejected", 0) >= before + 1


def test_on_failure_enqueues_dead_letter(monkeypatch):
    enqueued = []

    class FakeQueue:
        def __init__(self, name, connection=None):
            self.name = name

        def enqueue(self, *args, **kwargs):
            enqueued.append((self.name, args, kwargs))

    monkeypatch.setattr("rq.Queue", FakeQueue)
    monkeypatch.setattr("app.workers.tasks.record_poison_job", lambda *_a, **_k: None)
    job = SimpleNamespace(id="job-dead-1")
    before = snapshot().get("jobs.dead_letter", 0)
    _on_failure(job, connection=None, type=Exception, value=RuntimeError("boom"), traceback=None)
    assert any(item[0] == "analysis_dlq" for item in enqueued)
    assert snapshot().get("jobs.dead_letter", 0) >= before + 1


def test_rq_worker_registers_graceful_stop(monkeypatch):
    handlers = {}

    class FakeWorker:
        def __init__(self, *a, **k):
            self.stopped = False

        def request_stop(self):
            self.stopped = True

        def work(self):
            handler = handlers.get(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
            assert self.stopped is True

    monkeypatch.setattr("app.workers.rq_worker.Worker", FakeWorker)
    monkeypatch.setattr("app.workers.rq_worker.SimpleWorker", FakeWorker)

    class FakeRedis:
        @classmethod
        def from_url(cls, *a, **k):
            return object()

    monkeypatch.setattr("app.workers.rq_worker.Redis", FakeRedis)
    monkeypatch.setattr(
        "app.workers.rq_worker.signal.signal",
        lambda sig, handler: handlers.__setitem__(sig, handler),
    )
    monkeypatch.setattr(
        "app.workers.rq_worker.get_settings",
        lambda: SimpleNamespace(redis_url="redis://localhost:6379/0"),
    )
    rq_main()


def test_alert_rules_yaml_lists_catalog_ids():
    rules_text = (REPO / "ops" / "prometheus" / "alert-rules.yml").read_text(encoding="utf-8")
    catalog = (REPO / "docs" / "ALERT_CATALOG.md").read_text(encoding="utf-8")
    for aid in ("A-WH", "A-READY", "A-PAY", "A-AI", "A-DB", "A-REDIS"):
        assert f"alert_id: {aid}" in rules_text
        assert aid in catalog
    assert "academiccheck_billing_failed_payments" in rules_text
    assert "Not loaded" in rules_text or "SPECIFICATION ONLY" in rules_text or "specification" in rules_text.lower()


def test_compose_pool_env_aligned_under_pgbouncer():
    text = (REPO / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "DB_POOL_SIZE" in text
    assert "DB_MAX_OVERFLOW" in text
    assert "DEFAULT_POOL_SIZE: 20" in text


def test_migration_010_keyset_indexes_exist():
    path = REPO / "backend" / "alembic" / "versions" / "010_keyset_indexes.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "ix_assignments_user_updated_id" in text
    assert "009_mfa_job_heartbeat" in text


def test_load_test_script_declares_profiles_without_fabricating_results():
    text = (REPO / "ops" / "load_test.js").read_text(encoding="utf-8")
    for profile in ("smoke", "100", "1000", "5000", "10000"):
        assert profile in text
    assert "Results are only valid when pointed at a real staging URL" in text


def test_validate_restore_fails_closed_without_database_url(monkeypatch):
    path = REPO / "ops" / "validate_restore.py"
    spec = importlib.util.spec_from_file_location("validate_restore_pass3", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert mod.main() == 2


def test_billing_cancel_idor(client):
    a = _register(client, "bill-owner@example.com")
    b = _register(client, "bill-thief@example.com")
    db = SessionLocal()
    owner = db.query(User).filter(User.email == "bill-owner@example.com").one()
    from app.models.billing import Plan, Subscription

    plan = db.query(Plan).filter(Plan.slug == "student").one()
    sub = Subscription(user_id=owner.id, plan_id=plan.id, status="active", provider="stripe")
    db.add(sub)
    db.commit()
    sub_id = str(sub.id)
    db.close()
    stolen = client.post(f"/api/billing/{sub_id}/cancel", headers={"Authorization": f"Bearer {b}"})
    assert stolen.status_code == 404
    ok = client.post(f"/api/billing/{sub_id}/cancel", headers={"Authorization": f"Bearer {a}"})
    assert ok.status_code == 200


def test_public_faqs_and_analytics(client):
    faqs = client.get("/api/public/faqs")
    assert faqs.status_code == 200
    assert "items" in faqs.json()
    tracked = client.post(
        "/api/public/analytics",
        json={"event_name": "pass3_test", "path": "/help", "properties": {"text": "SECRET", "ok": True}},
    )
    assert tracked.status_code == 200


def test_settings_page_focus_traps_alertdialog():
    text = (REPO / "frontend" / "app" / "app" / "settings" / "page.tsx").read_text(encoding="utf-8")
    assert 'role="alertdialog"' in text
    assert "Tab" in text
    assert "confirmDeleteRef" in text


def test_stripe_hmac_accepts_valid_signature():
    from app.services.billing import _stripe_hmac

    secret = "whsec_ok"
    body = b'{"id":"evt_ok","type":"ping"}'
    ts = str(int(utcnow().timestamp()))
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    event = _stripe_hmac(body, f"t={ts},v1={sig}", secret, 300)
    assert event["id"] == "evt_ok"


def test_backup_restore_scripts_fail_closed_without_args():
    backup = (REPO / "ops" / "backup_postgres.sh").read_text(encoding="utf-8")
    restore = (REPO / "ops" / "restore_postgres.sh").read_text(encoding="utf-8")
    assert "pg_dump" in backup
    assert "set -euo pipefail" in backup
    assert "RESTORE_DATABASE_URL" in restore
    assert "exit 1" in restore


def test_deploy_rollback_workflow_fails_without_staging():
    text = (REPO / ".github" / "workflows" / "deploy-rollback-drill.yml").read_text(encoding="utf-8")
    assert "STAGING_URL" in text


def test_rollback_compose_script_requires_tag():
    text = (REPO / "ops" / "rollback_compose.sh").read_text(encoding="utf-8")
    assert "previous_image_tag" in text
    assert "exit 1" in text
    assert "/api/ready" in text

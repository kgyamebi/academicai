"""Billing reconcile + alert sink evidence (no live PSP)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.billing import Payment
from app.models.user import User
from app.services.billing_reconcile import reconcile_against_provider_snapshot


@pytest.fixture()
def reconcile_alert_sink(monkeypatch, tmp_path):
    inbox: list[dict] = []

    class Sink(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n).decode("utf-8") if n else ""
            inbox.append(json.loads(raw) if raw else {})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *_a):  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Sink)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    sink_file = tmp_path / "alerts.jsonl"
    monkeypatch.setenv("ALERT_WEBHOOK_URL", f"http://127.0.0.1:{port}/hook")
    monkeypatch.setenv("ALERT_SINK_FILE", str(sink_file))
    monkeypatch.setenv("ALERT_THROTTLE_SECONDS", "0")

    from app.config import get_settings
    from app.core import alerting

    get_settings.cache_clear()
    alerting.reset_alert_state_for_tests()
    yield inbox, sink_file, alerting
    server.shutdown()
    get_settings.cache_clear()


def test_reconcile_clean_empty_snapshot(client):
    db = SessionLocal()
    try:
        report = reconcile_against_provider_snapshot(db, [])
    finally:
        db.close()
    assert report["ok"] is True
    assert report["mismatch_count"] == 0


def test_reconcile_flags_missing_provider_and_fires_alert(client, reconcile_alert_sink):
    inbox, sink_file, alerting = reconcile_alert_sink
    db = SessionLocal()
    try:
        user = User(
            email="reconcile-alert@example.com",
            password_hash=hash_password("Str0ngPass1!"),
            full_name="R",
            is_guest=False,
        )
        db.add(user)
        db.flush()
        payment = Payment(
            user_id=user.id,
            provider="stripe",
            provider_payment_id="pi_test_missing_remote",
            amount_cents=100,
            currency="USD",
            status="successful",
            purpose="credits",
        )
        db.add(payment)
        db.commit()
        report = reconcile_against_provider_snapshot(db, [])
    finally:
        db.close()

    assert report["ok"] is False
    assert report["mismatch_count"] >= 1

    fired = alerting.fire_alert(
        "billing_reconcile_mismatch",
        title="Billing ledger reconciliation mismatch",
        detail=f"mismatch_count={report['mismatch_count']}",
        severity="critical",
        force=True,
    )
    assert fired is True
    assert any(item.get("alert_type") == "billing_reconcile_mismatch" for item in inbox)
    assert sink_file.exists()
    assert "billing_reconcile_mismatch" in sink_file.read_text(encoding="utf-8")


def test_fixture_snapshot_is_valid_json():
    path = Path(__file__).resolve().parents[2] / "ops" / "fixtures" / "billing_reconcile_snapshot.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)

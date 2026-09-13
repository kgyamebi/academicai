"""Alerting delivery + throttle tests (local webhook sink; no Grafana)."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


@pytest.fixture()
def alert_sink(monkeypatch, tmp_path):
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
    monkeypatch.setenv("ALERT_THROTTLE_SECONDS", "60")
    monkeypatch.setenv("ALERT_5XX_THRESHOLD", "3")
    monkeypatch.setenv("ALERT_5XX_WINDOW_SECONDS", "60")

    from app.config import get_settings

    get_settings.cache_clear()
    from app.core import alerting

    alerting.reset_alert_state_for_tests()
    yield inbox, sink_file, alerting
    server.shutdown()
    get_settings.cache_clear()


def test_payment_alert_delivers_to_webhook(alert_sink):
    inbox, sink_file, alerting = alert_sink
    ok = alerting.notify_payment_failure(provider="stripe", reason="bad sig", event_id="e1")
    assert ok is True
    time.sleep(0.15)
    assert any(i.get("alert_type") == "payment_failure" for i in inbox)
    lines = sink_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines and json.loads(lines[0])["alert_type"] == "payment_failure"


def test_5xx_spike_fires_once_at_threshold(alert_sink):
    inbox, _sink, alerting = alert_sink
    alerting.note_http_5xx(path="/x", status_code=500)
    alerting.note_http_5xx(path="/x", status_code=500)
    time.sleep(0.05)
    assert not any(i.get("alert_type") == "http_5xx_spike" for i in inbox)
    alerting.note_http_5xx(path="/x", status_code=503)
    time.sleep(0.15)
    spikes = [i for i in inbox if i.get("alert_type") == "http_5xx_spike"]
    assert len(spikes) == 1


def test_alert_throttle_batches_burst(alert_sink):
    inbox, _sink, alerting = alert_sink
    sent = 0
    for i in range(10):
        if alerting.fire_alert("worker_failure", title="same", detail=f"n={i}"):
            sent += 1
    time.sleep(0.15)
    assert sent == 1
    assert sum(1 for i in inbox if i.get("alert_type") == "worker_failure") == 1


def test_worker_and_backup_alerts(alert_sink):
    inbox, _sink, alerting = alert_sink
    alerting.notify_worker_failure(job_id="j1", error="killed")
    alerting.notify_backup_failure(error="pg_dump failed")
    time.sleep(0.2)
    types = {i.get("alert_type") for i in inbox}
    assert "worker_failure" in types
    assert "backup_failure" in types

"""Deliberately fire each alert type into a real local webhook sink and record proof.

Usage (from repo root):
  py -3.14 ops/verify_alerting.py

Does not require Slack/Discord. Points ALERT_WEBHOOK_URL at an ephemeral HTTP sink
started by this script. Also writes ops/alert_inbox.jsonl and ops/cert_alerting_proof.json.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SINK_PORT = int(os.environ.get("ALERT_VERIFY_PORT", "8765"))
inbox: list[dict] = []


class Sink(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw[:500]}
        inbox.append({"path": self.path, "body": body, "at": time.time()})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *_args):  # noqa: A003
        return


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    sink_file = ROOT / "ops" / "alert_inbox.jsonl"
    if sink_file.exists():
        sink_file.unlink()

    server = ThreadingHTTPServer(("127.0.0.1", SINK_PORT), Sink)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    os.environ["ALERT_WEBHOOK_URL"] = f"http://127.0.0.1:{SINK_PORT}/alert"
    os.environ["ALERT_SINK_FILE"] = str(sink_file)
    os.environ["ALERT_THROTTLE_SECONDS"] = "1"
    os.environ["ALERT_5XX_THRESHOLD"] = "3"
    os.environ["ALERT_5XX_WINDOW_SECONDS"] = "60"
    os.environ.setdefault("APP_ENV", "test")

    from app.config import get_settings

    get_settings.cache_clear()

    from app.core.alerting import (
        fire_alert,
        note_http_5xx,
        notify_backup_failure,
        notify_payment_failure,
        notify_unhandled_exception,
        notify_worker_failure,
        reset_alert_state_for_tests,
    )

    reset_alert_state_for_tests()
    results: list[dict] = []

    # 1) 5xx spike
    for _ in range(3):
        note_http_5xx(path="/api/ready", status_code=500)
    time.sleep(0.25)
    results.append({"trigger": "http_5xx_spike", "inbox_after": len(inbox)})

    # 2) payment/webhook failure
    notify_payment_failure(provider="stripe", reason="verify: forged signature", event_id="evt_verify")
    time.sleep(0.15)
    results.append({"trigger": "payment_failure", "inbox_after": len(inbox)})

    # 3) worker failure
    notify_worker_failure(job_id="job-verify-kill", error="verify: worker killed mid-job", stage="verify")
    time.sleep(0.15)
    results.append({"trigger": "worker_failure", "inbox_after": len(inbox)})

    # 4) backup failure (same path as ops/backup_postgres.sh notify_fail)
    notify_backup_failure(error="verify: DATABASE_URL missing / pg_dump failed")
    time.sleep(0.15)
    results.append({"trigger": "backup_failure", "inbox_after": len(inbox)})

    # 5) unhandled exception path (API middleware)
    notify_unhandled_exception(
        path="/api/verify-boom",
        error="verify: RuntimeError boom",
        stack="Traceback (verify)\nRuntimeError: boom\n",
        request_id="verify-req-1",
    )
    time.sleep(0.15)
    results.append({"trigger": "unhandled_exception", "inbox_after": len(inbox)})

    # 6) throttle: burst must not flood
    reset_alert_state_for_tests()
    before = len(inbox)
    for i in range(20):
        fire_alert(
            "payment_failure",
            title="Payment/webhook failure (stripe)",
            detail=f"burst {i}",
            severity="critical",
        )
    time.sleep(0.25)
    throttled_extra = len(inbox) - before
    results.append({"trigger": "throttle_burst", "extra_delivered": throttled_extra, "expect_lte": 1})

    types = {
        item["body"].get("alert_type")
        for item in inbox
        if isinstance(item.get("body"), dict) and item["body"].get("alert_type")
    }
    required = {"http_5xx_spike", "payment_failure", "worker_failure", "backup_failure", "unhandled_exception"}
    missing = sorted(required - types)

    fire_alert("verify_file_sink", title="File sink check", detail="dual delivery", force=True)
    time.sleep(0.15)
    file_lines = sink_file.read_text(encoding="utf-8").strip().splitlines() if sink_file.exists() else []

    received_types = sorted(types | ({"verify_file_sink"} if any(
        (i.get("body") or {}).get("alert_type") == "verify_file_sink" for i in inbox
    ) else set()))

    proof = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "webhook_url": os.environ["ALERT_WEBHOOK_URL"],
        "sink_file": str(sink_file),
        "sink_http_received": len(inbox),
        "sink_file_lines": len(file_lines),
        "alert_types_received": received_types,
        "required": sorted(required),
        "missing": missing,
        "results": results,
        "sample_payloads": [i["body"] for i in inbox[:8]],
        "throttle_extra_delivered": throttled_extra,
        "grafana": False,
        "prometheus": False,
        "destination": "local_http_webhook_sink_compatible_with_slack_discord",
        "pass": not missing and len(inbox) >= 5 and throttled_extra <= 1 and len(file_lines) >= 1,
    }
    out = ROOT / "ops" / "cert_alerting_proof.json"
    out.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                k: proof[k]
                for k in (
                    "pass",
                    "sink_http_received",
                    "missing",
                    "throttle_extra_delivered",
                    "alert_types_received",
                )
            },
            indent=2,
        )
    )

    server.shutdown()
    return 0 if proof["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

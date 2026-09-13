"""Fire readiness alerts to a local sink. Not Grafana Cloud or PagerDuty."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PORT = 8033
COMPOSE = ROOT / "docker-compose.cert.yml"
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
inbox: list[dict] = []


class Sink(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else ""
        inbox.append({"path": self.path, "body": body[:1000], "at": time.time()})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt, *args):  # noqa: A003
        return


def status(path: str) -> int | None:
    try:
        with urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=8) as resp:
            return resp.status
    except Exception as exc:
        if hasattr(exc, "code"):
            return int(exc.code)
        return None


def main() -> int:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "production",
            "REQUIRE_QUEUE": "true",
            "DATABASE_URL": PG,
            "REDIS_URL": REDIS,
            "APP_SECRET_KEY": "cert-production-secret",
            "JWT_SECRET_KEY": "cert-jwt-secret-key-32-bytes-min-xx",
            "FIELD_ENCRYPTION_KEY": "cert-field-encryption-key-material",
            "PYTHONPATH": str(BACKEND),
        }
    )
    sink = ThreadingHTTPServer(("127.0.0.1", 8034), Sink)
    import threading

    threading.Thread(target=sink.serve_forever, daemon=True).start()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    events = []
    try:
        deadline = time.time() + 30
        while time.time() < deadline and status("/api/live") != 200:
            time.sleep(0.3)
        events.append({"probe": "baseline_ready", "status": status("/api/ready")})
        subprocess.run(["docker", "compose", "-f", str(COMPOSE), "stop", "redis"], check=True)
        time.sleep(1)
        redis_ready = status("/api/ready")
        events.append({"probe": "redis_down_ready", "status": redis_ready})
        if redis_ready == 503:
            # local alert manager analogue
            urlopen("http://127.0.0.1:8034/alert", timeout=2, data=b'{"alert":"redis_down","severity":"page"}')
            events.append({"probe": "alert_posted", "status": 200})
        subprocess.run(["docker", "compose", "-f", str(COMPOSE), "start", "redis"], check=True)
        time.sleep(3)
        events.append({"probe": "redis_recovered_ready", "status": status("/api/ready")})
        payload = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "events": events,
            "sink_received": len(inbox),
            "grafana": False,
            "pagerduty": False,
            "alertmanager": False,
            "local_sink_alert": any(e.get("probe") == "alert_posted" for e in events),
            "pass_local_ready_alert": redis_ready == 503 and len(inbox) >= 1,
        }
        out = ROOT / "ops" / "cert_alert_fire.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0 if payload["pass_local_ready_alert"] else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        sink.shutdown()
        subprocess.run(["docker", "compose", "-f", str(COMPOSE), "start"], check=False)


if __name__ == "__main__":
    raise SystemExit(main())

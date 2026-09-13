"""Blue-green traffic switch and automatic rollback on failed health. Local processes, not a cloud LB."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
BLUE = 8031
GREEN = 8032
EDGE = 8030
state = {"active": "blue", "rollback": False, "seen": []}


def spawn(port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "test",
            "DATABASE_URL": PG,
            "REDIS_URL": REDIS,
            "APP_SECRET_KEY": "cert-secret",
            "JWT_SECRET_KEY": "cert-jwt-secret-key-32-bytes-min",
            "PYTHONPATH": str(BACKEND),
        }
    )
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_live(port: int) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urlopen(f"http://127.0.0.1:{port}/api/live", timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"port {port} not live")


def proxy_target() -> int:
    return BLUE if state["active"] == "blue" else GREEN


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        port = proxy_target()
        try:
            with urlopen(f"http://127.0.0.1:{port}{self.path}", timeout=3) as resp:
                body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("X-Upstream", state["active"])
                self.end_headers()
                self.wfile.write(body)
                state["seen"].append({"upstream": state["active"], "status": resp.status, "path": self.path})
        except Exception:
            self.send_response(502)
            self.end_headers()
            state["seen"].append({"upstream": state["active"], "status": 502, "path": self.path})

    def log_message(self, fmt, *args):  # noqa: A003
        return


def health_watch(stop: threading.Event) -> None:
    while not stop.is_set():
        port = proxy_target()
        try:
            with urlopen(f"http://127.0.0.1:{port}/api/live", timeout=1) as resp:
                ok = resp.status == 200
        except Exception:
            ok = False
        if not ok and state["active"] == "green":
            state["active"] = "blue"
            state["rollback"] = True
        time.sleep(0.15)


def main() -> int:
    blue = spawn(BLUE)
    green = spawn(GREEN)
    stop = threading.Event()
    httpd = ThreadingHTTPServer(("127.0.0.1", EDGE), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    watch = threading.Thread(target=health_watch, args=(stop,), daemon=True)
    try:
        wait_live(BLUE)
        wait_live(GREEN)
        thread.start()
        watch.start()
        # traffic on blue
        for _ in range(20):
            with urlopen(f"http://127.0.0.1:{EDGE}/api/live", timeout=2) as resp:
                assert resp.status == 200
        state["active"] = "green"
        time.sleep(0.2)
        switched = 0
        for _ in range(20):
            with urlopen(f"http://127.0.0.1:{EDGE}/api/live", timeout=2) as resp:
                if resp.headers.get("X-Upstream") == "green" and resp.status == 200:
                    switched += 1
        # break green
        green.kill()
        green.wait(timeout=5)
        deadline = time.time() + 8
        while time.time() < deadline and not state["rollback"]:
            try:
                urlopen(f"http://127.0.0.1:{EDGE}/api/live", timeout=2).read()
            except Exception:
                pass
            time.sleep(0.2)
        recovered = 0
        errors = 0
        for _ in range(30):
            try:
                with urlopen(f"http://127.0.0.1:{EDGE}/api/live", timeout=2) as resp:
                    if resp.status == 200 and resp.headers.get("X-Upstream") == "blue":
                        recovered += 1
                    elif resp.status >= 400:
                        errors += 1
            except Exception:
                errors += 1
        payload = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "edge": f"http://127.0.0.1:{EDGE}",
            "blue": BLUE,
            "green": GREEN,
            "green_switch_200s": switched,
            "automatic_rollback": state["rollback"],
            "recovered_blue_200s": recovered,
            "errors_after_rollback": errors,
            "pass": switched >= 15 and state["rollback"] and recovered >= 20 and errors == 0,
            "not_run": ["cloud_lb", "kubernetes", "canary_percent", "migration_rollback"],
        }
        out = ROOT / "ops" / "cert_bluegreen_results.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0 if payload["pass"] else 1
    finally:
        stop.set()
        httpd.shutdown()
        blue.terminate()
        if green.poll() is None:
            green.terminate()
        try:
            blue.wait(timeout=5)
        except subprocess.TimeoutExpired:
            blue.kill()


if __name__ == "__main__":
    raise SystemExit(main())

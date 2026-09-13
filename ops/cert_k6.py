"""k6 via Docker against a live local API. Does not claim 1k/10k/50k unless those profiles actually finish."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PORT = int(os.environ.get("CERT_K6_PORT", "8014"))
BASE = f"http://127.0.0.1:{PORT}"
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
PROFILE = os.environ.get("CERT_K6_PROFILE", "100")
SCRIPT = ROOT / "ops" / "load_test.js"


def main() -> int:
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
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
            "--workers",
            os.environ.get("CERT_UVICORN_WORKERS", "4"),
        ],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                with urlopen(f"{BASE}/api/live", timeout=1) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.3)
        else:
            raise RuntimeError("API did not become live")

        summary_path = ROOT / "ops" / "cert_k6_summary.json"
        cmd = [
            "docker",
            "run",
            "--rm",
            "--add-host=host.docker.internal:host-gateway",
            "-v",
            f"{SCRIPT}:/scripts/load_test.js:ro",
            "grafana/k6:latest",
            "run",
            "--summary-export=/tmp/summary.json",
            "-e",
            f"BASE_URL=http://host.docker.internal:{PORT}",
            "-e",
            f"PROFILE={PROFILE}",
            "/scripts/load_test.js",
        ]
        # summary-export inside container is discarded; capture stdout instead via --out json
        cmd = [
            "docker",
            "run",
            "--rm",
            "--add-host=host.docker.internal:host-gateway",
            "-v",
            f"{str(ROOT / 'ops')}:/scripts:ro",
            "-v",
            f"{str(ROOT / 'ops')}:/out",
            "grafana/k6:latest",
            "run",
            "--summary-export=/out/cert_k6_summary.json",
            "-e",
            f"BASE_URL=http://host.docker.internal:{PORT}",
            "-e",
            f"PROFILE={PROFILE}",
            "/scripts/load_test.js",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        payload = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "profile": PROFILE,
            "base": BASE,
            "exit_code": result.returncode,
            "stdout_tail": (result.stdout or "")[-4000:],
            "stderr_tail": (result.stderr or "")[-2000:],
            "not_run": [n for n in ("1000", "5000", "10000", "50000") if n != PROFILE],
        }
        if summary_path.exists():
            try:
                payload["k6_summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload["k6_summary"] = "unreadable"
        out = ROOT / "ops" / "cert_k6_results.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({k: payload[k] for k in ("profile", "exit_code", "not_run")}, indent=2))
        print((result.stdout or "")[-1500:])
        return 0 if result.returncode == 0 else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())

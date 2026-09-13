"""Host chaos against the certification compose stack. Records observed HTTP status only."""

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
PORT = 8012
BASE = f"http://127.0.0.1:{PORT}"
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
COMPOSE = ROOT / "docker-compose.cert.yml"


def http_status(path: str) -> int | None:
    try:
        with urlopen(f"{BASE}{path}", timeout=8) as resp:
            return resp.status
    except Exception as exc:  # noqa: BLE001
        code = getattr(getattr(exc, "code", None), "real", None)
        if hasattr(exc, "code"):
            return int(exc.code)
        return None


def compose(*args: str) -> None:
    subprocess.run(["docker", "compose", "-f", str(COMPOSE), *args], check=True)


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
    log_path = ROOT / "tmp" / "cert_chaos_api.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=BACKEND,
        env=env,
        stdout=log,
        stderr=log,
    )
    results = {}
    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            status = http_status("/api/live")
            if status == 200:
                break
            time.sleep(0.3)
        results["baseline_live"] = http_status("/api/live")
        results["baseline_ready"] = http_status("/api/ready")

        compose("stop", "redis")
        time.sleep(1)
        results["redis_down_live"] = http_status("/api/live")
        results["redis_down_ready"] = http_status("/api/ready")
        compose("start", "redis")
        time.sleep(8)
        results["redis_recovered_ready"] = http_status("/api/ready")

        compose("stop", "postgres")
        time.sleep(1)
        results["postgres_down_live"] = http_status("/api/live")
        results["postgres_down_ready"] = http_status("/api/ready")
        compose("start", "postgres")
        time.sleep(8)
        results["postgres_recovered_ready"] = http_status("/api/ready")

        payload = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "api": BASE,
            "results": results,
            "expect": {
                "live_stays_200": results.get("postgres_down_live") == 200 and results.get("redis_down_live") == 200,
                "ready_503_when_redis_down": results.get("redis_down_ready") == 503,
                "ready_503_when_postgres_down": results.get("postgres_down_ready") == 503,
                "redis_recovered_ready": results.get("redis_recovered_ready") == 200,
                "postgres_recovered_ready": results.get("postgres_recovered_ready") == 200,
            },
            "not_run": ["ai_provider_kill", "billing_provider_kill", "network_partition", "storage_kill"],
        }
        payload["pass"] = all(payload["expect"].values())
        out = ROOT / "ops" / "cert_chaos_results.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0 if payload["pass"] else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        # always try to bring stack back
        subprocess.run(["docker", "compose", "-f", str(COMPOSE), "start"], check=False)


if __name__ == "__main__":
    raise SystemExit(main())

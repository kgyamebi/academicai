"""Start N uvicorn API processes on 18001+ for the local nginx load balancer."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
COUNT = int(os.environ.get("CERT_API_INSTANCES", "10"))
BASE_PORT = int(os.environ.get("CERT_API_BASE_PORT", "18001"))


def main() -> int:
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["DATABASE_URL"] = env.get(
        "CERT_DATABASE_URL",
        "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56432/academiccheck",
    )
    env["REDIS_URL"] = env.get("CERT_REDIS_URL", "redis://127.0.0.1:56380/0")
    env["APP_SECRET_KEY"] = "cert-secret-key-32-bytes-minimum-ok"
    env["JWT_SECRET_KEY"] = "cert-jwt-secret-key-32-bytes-min"
    env["PYTHONPATH"] = str(BACKEND)
    env["REQUIRE_QUEUE"] = "false"
    if os.environ.get("CERT_USE_REPLICA") == "1":
        env["DATABASE_READ_URL"] = os.environ.get(
            "CERT_REPLICA_URL",
            "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56433/academiccheck",
        )
    log_dir = ROOT / "tmp" / "cert_api"
    log_dir.mkdir(parents=True, exist_ok=True)
    procs = []
    for i in range(COUNT):
        port = BASE_PORT + i
        log = (log_dir / f"api-{port}.log").open("w", encoding="utf-8")
        procs.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--workers",
                    "1",
                ],
                cwd=BACKEND,
                env=env,
                stdout=log,
                stderr=log,
            )
        )
    live = 0
    deadline = time.time() + 60
    while time.time() < deadline and live < COUNT:
        live = 0
        for i in range(COUNT):
            port = BASE_PORT + i
            try:
                with urlopen(f"http://127.0.0.1:{port}/api/live", timeout=1) as resp:
                    if resp.status == 200:
                        live += 1
            except Exception:
                pass
        time.sleep(0.5)
    print(f"api_instances_live={live}/{COUNT}", flush=True)
    pids_path = ROOT / "tmp" / "cert_api" / "pids.txt"
    pids_path.write_text("\n".join(str(p.pid) for p in procs), encoding="utf-8")
    if live < 1:
        for proc in procs:
            proc.terminate()
        return 2
    try:
        while True:
            time.sleep(30)
            if all(proc.poll() is not None for proc in procs):
                break
    except KeyboardInterrupt:
        pass
    finally:
        for proc in procs:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    return 0 if live == COUNT else 1


if __name__ == "__main__":
    raise SystemExit(main())

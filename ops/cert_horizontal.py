"""Two local uvicorn processes. Not a 50-instance load-balancer certificate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import urlopen

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PORTS = [8015, 8016]
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p / 100))]


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
    procs = []
    for port in PORTS:
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
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
    try:
        for port in PORTS:
            deadline = time.time() + 30
            while time.time() < deadline:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/api/live", timeout=1) as resp:
                        if resp.status == 200:
                            break
                except Exception:
                    time.sleep(0.2)
            else:
                raise RuntimeError(f"port {port} not live")

        samples: list[float] = []
        codes: dict[int, int] = {}
        errors = 0

        def one(i: int) -> tuple[float, int]:
            port = PORTS[i % len(PORTS)]
            start = time.perf_counter()
            with httpx.Client(timeout=10) as client:
                response = client.get(f"http://127.0.0.1:{port}/api/live")
            return (time.perf_counter() - start) * 1000, response.status_code

        with ThreadPoolExecutor(max_workers=80) as pool:
            futs = [pool.submit(one, i) for i in range(400)]
            for fut in as_completed(futs):
                ms, code = fut.result()
                samples.append(ms)
                codes[code] = codes.get(code, 0) + 1
                if code >= 400:
                    errors += 1
        payload = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "instances": PORTS,
            "lb": "client_round_robin_not_nginx",
            "requests": len(samples),
            "p50_ms": round(pct(samples, 50), 3),
            "p95_ms": round(pct(samples, 95), 3),
            "p99_ms": round(pct(samples, 99), 3),
            "error_rate": round(errors / max(len(samples), 1), 4),
            "status_counts": codes,
            "not_run": ["instances_5", "instances_10", "instances_50", "nginx", "traefik", "cloud_lb", "sticky_sessions"],
        }
        out = ROOT / "ops" / "cert_horizontal_results.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        for proc in procs:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())

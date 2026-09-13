"""Live uvicorn HTTP bench against certification Postgres. Not a 50k-VU cluster test."""

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
PORT = 8013
BASE = f"http://127.0.0.1:{PORT}"
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
WORKERS = int(os.environ.get("CERT_UVICORN_WORKERS", "4"))


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p / 100))]


def burst(client: httpx.Client, path: str, in_flight: int, total: int) -> dict:
    samples: list[float] = []
    errors = 0

    def one() -> tuple[float, int]:
        start = time.perf_counter()
        response = client.get(f"{BASE}{path}")
        return (time.perf_counter() - start) * 1000, response.status_code

    with ThreadPoolExecutor(max_workers=in_flight) as pool:
        futs = [pool.submit(one) for _ in range(total)]
        for fut in as_completed(futs):
            ms, code = fut.result()
            samples.append(ms)
            if code >= 400:
                errors += 1
    return {
        "path": path,
        "in_flight": in_flight,
        "requests": total,
        "p50_ms": round(pct(samples, 50), 3),
        "p95_ms": round(pct(samples, 95), 3),
        "p99_ms": round(pct(samples, 99), 3),
        "error_rate": round(errors / max(len(samples), 1), 4),
    }


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
            str(WORKERS),
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
                time.sleep(0.2)
        else:
            raise RuntimeError("API did not become live")
        results = {}
        with httpx.Client(timeout=15) as client:
            for in_flight, total in ((1, 200), (50, 500), (100, 1000), (250, 1000), (500, 1000)):
                results[f"live_{in_flight}"] = burst(client, "/api/live", in_flight, total)
            results["ready_1"] = burst(client, "/api/ready", 1, 200)
            results["ready_50"] = burst(client, "/api/ready", 50, 200)
        payload = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target": BASE,
            "uvicorn_workers": WORKERS,
            "database": "postgresql-16 docker",
            "results": results,
            "slo": {
                "p95_ms": 500,
                "p99_ms": 1000,
                "error_rate": 0.01,
            },
            "not_run": ["1000_concurrent_users", "10000_concurrent_users", "50000_concurrent_users", "k6_authenticated"],
        }
        live100 = results.get("live_100") or {}
        payload["live_100_meets_slo"] = (
            live100.get("p95_ms", 9999) < 500
            and live100.get("p99_ms", 9999) < 1000
            and live100.get("error_rate", 1) < 0.01
        )
        out = ROOT / "ops" / "cert_http_results.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())

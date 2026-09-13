"""HTTP bench against a live uvicorn process. Records only what this host can sustain."""

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
PORT = 8011
BASE = f"http://127.0.0.1:{PORT}"


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p / 100))]


def wait_live(timeout: float = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(f"{BASE}/api/live", timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("API did not become live")


def burst(client: httpx.Client, in_flight: int, total: int) -> dict:
    samples: list[float] = []
    errors = 0

    def one() -> tuple[float, int]:
        start = time.perf_counter()
        response = client.get(f"{BASE}/api/live")
        return (time.perf_counter() - start) * 1000, response.status_code

    with ThreadPoolExecutor(max_workers=in_flight) as pool:
        futs = [pool.submit(one) for _ in range(total)]
        for fut in as_completed(futs):
            ms, code = fut.result()
            samples.append(ms)
            if code != 200:
                errors += 1
    return {
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
            "APP_SECRET_KEY": "bench-secret",
            "JWT_SECRET_KEY": "bench-jwt-secret-key-32-bytes-min",
            "DATABASE_URL": "sqlite:///./bench_http.db",
        }
    )
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_live()
        results = {}
        with httpx.Client(timeout=10) as client:
            for in_flight, total in ((1, 200), (50, 500), (100, 1000), (250, 1000)):
                results[str(in_flight)] = burst(client, in_flight, total)
        payload = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target": BASE,
            "endpoint": "/api/live",
            "results": results,
            "not_run": ["1000_in_flight", "10000_in_flight", "50000_in_flight", "authenticated_routes"],
        }
        out = ROOT / "ops" / "bench_http_results.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())

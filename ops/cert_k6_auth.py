"""Authenticated k6 against the local nginx load balancer. Tiers not executed are not_reached."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
BASE = os.environ.get("CERT_LB_URL", "http://127.0.0.1:18080")
PROFILES = [p.strip() for p in os.environ.get("CERT_K6_PROFILES", "100,1000,5000,10000").split(",") if p.strip()]
EMAIL = os.environ.get("CERT_K6_EMAIL", "scale-k6@example.com")
PASSWORD = os.environ.get("CERT_K6_PASSWORD", "password12")
SCRIPT = ROOT / "ops" / "load_test_auth.js"


def ensure_user() -> None:
    body = json.dumps({"email": EMAIL, "password": PASSWORD, "full_name": "K6"}).encode()
    req = Request(f"{BASE}/api/auth/register", data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception:
        login = Request(
            f"{BASE}/api/auth/login",
            data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(login, timeout=10) as resp:
            if resp.status != 200:
                raise RuntimeError("k6 user login failed")


def run_profile(profile: str) -> dict:
    summary = ROOT / "ops" / f"cert_k6_summary_{profile}.json"
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
        f"--summary-export=/out/cert_k6_summary_{profile}.json",
        "-e",
        f"BASE_URL={BASE.replace('127.0.0.1', 'host.docker.internal')}",
        "-e",
        f"PROFILE={profile}",
        "-e",
        f"EMAIL={EMAIL}",
        "-e",
        f"PASSWORD={PASSWORD}",
        "/scripts/load_test_auth.js",
    ]
    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0
    summary_data = None
    if summary.exists():
        try:
            summary_data = json.loads(summary.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            summary_data = "unreadable"
    metrics = {}
    if isinstance(summary_data, dict):
        http_req = (summary_data.get("metrics") or {}).get("http_req_duration") or {}
        failed = (summary_data.get("metrics") or {}).get("http_req_failed") or {}
        values = http_req.get("values") or http_req
        metrics = {
            "p95_ms": values.get("p(95)") or values.get("avg"),
            "p99_ms": values.get("p(99)"),
            "error_rate": (failed.get("values") or failed).get("rate"),
        }
    return {
        "profile_vus": profile,
        "exit_code": result.returncode,
        "elapsed_s": round(elapsed, 3),
        "metrics": metrics,
        "slo_p95_500ms": (metrics.get("p95_ms") is not None and metrics["p95_ms"] < 500),
        "slo_error_lt_1pct": (metrics.get("error_rate") is not None and metrics["error_rate"] < 0.01),
        "stdout_tail": (result.stdout or "")[-2500:],
        "stderr_tail": (result.stderr or "")[-1500:],
        "hardware_start_failed": "ENOENT" in (result.stderr or "") or result.returncode == 127,
    }


def main() -> int:
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base": BASE,
        "profiles": {},
        "not_reached": [],
    }
    existing_path = ROOT / "ops" / "cert_k6_load.json"
    if existing_path.exists():
        try:
            prev = json.loads(existing_path.read_text(encoding="utf-8"))
            payload["profiles"].update(prev.get("profiles") or {})
        except json.JSONDecodeError:
            pass
    try:
        ensure_user()
    except Exception as exc:
        payload["setup_error"] = str(exc)
        payload["not_reached"] = PROFILES
        (ROOT / "ops" / "cert_k6_load.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 1
    for profile in PROFILES:
        print(f"=== k6 authenticated {profile} VU ===", flush=True)
        try:
            entry = run_profile(profile)
        except Exception as exc:
            entry = {"profile_vus": profile, "error": str(exc)}
            payload["not_reached"].append({"tier": profile, "reason": "not_started", "detail": str(exc)})
            payload["profiles"][profile] = entry
            continue
        payload["profiles"][profile] = entry
        if entry.get("hardware_start_failed"):
            payload["not_reached"].append({"tier": profile, "reason": "hardware_or_k6_unavailable"})
            break
        if entry.get("exit_code") not in {0, 99}:
            # k6 99 = threshold fail; still a completed run
            if entry.get("exit_code") != 99:
                payload["not_reached"].append({"tier": profile, "reason": f"k6_exit_{entry.get('exit_code')}"})
    # 50k is never silently blank
    if "50000" not in payload["profiles"]:
        payload["not_reached"].append({"tier": "50000", "reason": "not_executed"})
    out = ROOT / "ops" / "cert_k6_load.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"profiles": list(payload["profiles"]), "not_reached": payload["not_reached"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

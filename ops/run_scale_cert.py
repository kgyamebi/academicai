"""Provision the local scale stack and run every cert that can be proven on this machine."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "ops" / "docker-compose.scale.yml"
PY = sys.executable


def run(cmd: list[str], env: dict | None = None, timeout: int | None = None) -> int:
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env or os.environ.copy(), timeout=timeout)
    return proc.returncode


def wait_tcp(url: str, timeout: int = 120) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    return True
        except Exception:
            time.sleep(2)
    return False


def main() -> int:
    env = os.environ.copy()
    env.setdefault(
        "CERT_DATABASE_URL",
        "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56432/academiccheck",
    )
    env.setdefault(
        "CERT_PGBOUNCER_URL",
        "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56434/academiccheck",
    )
    env.setdefault(
        "CERT_REPLICA_URL",
        "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56433/academiccheck",
    )
    env.setdefault("CERT_REDIS_URL", "redis://127.0.0.1:56380/0")
    summary: dict = {"measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "steps": {}}

    code = run(["docker", "compose", "-f", str(COMPOSE), "up", "-d"], env)
    summary["steps"]["compose_up"] = code
    if code != 0:
        (ROOT / "ops" / "cert_scale_orchestrator.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return code

    print("waiting for postgres primary...", flush=True)
    # pg_isready via docker
    deadline = time.time() + 180
    while time.time() < deadline:
        probe = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE),
                "exec",
                "-T",
                "pg-primary",
                "pg_isready",
                "-U",
                "academiccheck",
            ],
            cwd=str(ROOT),
            capture_output=True,
        )
        if probe.returncode == 0:
            break
        time.sleep(3)
    else:
        summary["steps"]["primary_ready"] = "timeout"
        (ROOT / "ops" / "cert_scale_orchestrator.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return 2

    for name, script in (
        ("load_rows", "ops/cert_scale_load_rows.py"),
        ("explain", "ops/cert_scale_explain.py"),
        ("worker_scale", "ops/cert_worker_scale.py"),
        ("llm_heuristic", "ops/cert_llm_load.py"),
        ("storage_volume", "ops/cert_storage_volume.py"),
    ):
        summary["steps"][name] = run([PY, str(ROOT / script)], env)

    fleet = subprocess.Popen([PY, str(ROOT / "ops" / "cert_api_fleet.py")], cwd=str(ROOT), env=env)
    time.sleep(20)
    live = False
    try:
        with urlopen("http://127.0.0.1:18001/api/live", timeout=2) as resp:
            live = resp.status == 200
    except Exception:
        live = False
    summary["steps"]["api_fleet_live"] = live
    if live:
        summary["steps"]["k6_auth"] = run([PY, str(ROOT / "ops" / "cert_k6_auth.py")], env)
        summary["steps"]["cdn_cache"] = run([PY, str(ROOT / "ops" / "cert_cdn_cache.py")], env)
    else:
        summary["steps"]["k6_auth"] = "skipped_no_api"
        summary["steps"]["cdn_cache"] = "skipped_no_api"
    fleet.terminate()
    try:
        fleet.wait(timeout=15)
    except subprocess.TimeoutExpired:
        fleet.kill()

    (ROOT / "ops" / "cert_scale_orchestrator.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

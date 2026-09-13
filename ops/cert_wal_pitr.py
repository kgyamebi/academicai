"""WAL-based point-in-time restore against local Postgres 16.

Proves restore to a timestamp BETWEEN two committed writes (row A kept, row B absent).
This is the engine mechanism managed PITR wraps. Managed-provider PITR itself stays
UNPROVEN without a live cloud account.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "ops" / "docker-compose.pitr.yml"
CONTAINER = "academiccheck-pitr-pg"


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["docker", *args], check=False, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"docker {args!r} failed rc={proc.returncode}: {(proc.stderr or proc.stdout or '')[-800:]}")
    return proc


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return docker("compose", "-f", str(COMPOSE), *args, check=check)


def psql(sql: str) -> str:
    proc = docker(
        "exec",
        CONTAINER,
        "psql",
        "-U",
        "pitr",
        "-d",
        "pitr",
        "-v",
        "ON_ERROR_STOP=1",
        "-t",
        "-A",
        "-c",
        sql,
    )
    return (proc.stdout or "").strip()


def wait_ready(timeout: int = 90) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        proc = docker(
            "exec",
            CONTAINER,
            "psql",
            "-U",
            "pitr",
            "-d",
            "pitr",
            "-t",
            "-A",
            "-c",
            "SELECT 1",
            check=False,
        )
        last = (proc.stdout or proc.stderr or "").strip()
        if proc.returncode == 0 and last.splitlines()[-1:] == ["1"]:
            return
        time.sleep(1)
    raise RuntimeError(f"pitr postgres not ready: {last}")


def wait_recovered(timeout: int = 90) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        proc = docker(
            "exec",
            CONTAINER,
            "psql",
            "-U",
            "pitr",
            "-d",
            "pitr",
            "-t",
            "-A",
            "-c",
            "SELECT pg_is_in_recovery();",
            check=False,
        )
        last = (proc.stdout or proc.stderr or "").strip()
        if proc.returncode == 0 and last.lower() in {"f", "false"}:
            return
        time.sleep(1)
    raise RuntimeError(f"recovery did not promote: {last}")


def run_once() -> dict:
    compose("down", "-v", check=False)
    compose("up", "-d")
    wait_ready()
    docker("exec", "-u", "root", CONTAINER, "mkdir", "-p", "/wal_archive", "/basebackup")
    docker("exec", "-u", "root", CONTAINER, "chown", "-R", "postgres:postgres", "/wal_archive", "/basebackup")
    # Archive command failed during initdb (volume was root-owned). Restart now that it is writable.
    compose("restart")
    wait_ready()

    psql("CREATE TABLE pitr_probe (id int PRIMARY KEY, note text NOT NULL);")
    psql("CHECKPOINT;")
    psql("SELECT pg_switch_wal();")
    docker("exec", "-u", "postgres", CONTAINER, "rm", "-rf", "/basebackup/base")
    docker(
        "exec",
        "-u",
        "postgres",
        CONTAINER,
        "pg_basebackup",
        "-D",
        "/basebackup/base",
        "-U",
        "pitr",
        "--checkpoint=fast",
        "--wal-method=none",
    )
    psql("INSERT INTO pitr_probe VALUES (1, 'before-target');")
    psql("SELECT pg_switch_wal();")
    time.sleep(2)
    target = psql("SELECT clock_timestamp();")
    time.sleep(3)
    psql("INSERT INTO pitr_probe VALUES (2, 'after-target');")
    psql("SELECT pg_switch_wal();")
    psql("CHECKPOINT;")
    time.sleep(2)
    before_restore = psql("SELECT string_agg(id::text, ',' ORDER BY id) FROM pitr_probe;")

    compose("stop")
    data_vol = _volume("pitr_pg_data")
    base_vol = _volume("pitr_basebackup")
    restore_cmd = "restore_command = 'cp /wal_archive/%f %p'"
    auto_conf = (
        f"{restore_cmd}\n"
        f"recovery_target_time = '{target}'\n"
        "recovery_target_action = 'promote'\n"
        "recovery_target_inclusive = on\n"
    )
    write_conf = (
        "rm -rf /data/* /data/.[!.]* 2>/dev/null; "
        "cp -a /basebackup/base/. /data/; "
        "touch /data/recovery.signal; "
        "cat >> /data/postgresql.auto.conf"
    )
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "-v",
            f"{data_vol}:/data",
            "-v",
            f"{base_vol}:/basebackup",
            "alpine:3.20",
            "sh",
            "-c",
            write_conf,
        ],
        input=auto_conf,
        check=True,
        capture_output=True,
        text=True,
    )
    compose("start")
    wait_ready()
    wait_recovered()
    ids = psql("SELECT string_agg(id::text, ',' ORDER BY id) FROM pitr_probe;")
    notes = psql("SELECT string_agg(note, ',' ORDER BY id) FROM pitr_probe;")
    compose("down", "-v")
    ok = ids == "1" and "before-target" in notes and "after-target" not in notes
    return {
        "recovery_target_time": target,
        "ids_before_restore": before_restore,
        "ids_after_pitr": ids,
        "notes_after_pitr": notes,
        "kept_row_a": ids == "1" or (ids or "").startswith("1"),
        "excluded_row_b": "2" not in (ids or "").split(","),
        "ok": ok,
    }


def _volume(logical: str) -> str:
    proc = docker("volume", "ls", "--format", "{{.Name}}")
    names = [line.strip() for line in (proc.stdout or "").splitlines() if logical in line]
    if not names:
        # compose project prefix typically directory name
        guessed = f"ops_{logical}"
        return guessed
    # Prefer exact suffix match
    for name in names:
        if name.endswith(logical) or name.endswith("_" + logical):
            return name
    return names[0]


def main() -> int:
    runs = [run_once(), run_once()]
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": "postgresql-16-alpine",
        "managed_provider_pitr": False,
        "consecutive_runs": 2,
        "runs": runs,
        "pass": all(run["ok"] for run in runs),
        "note": "Local WAL replay only. RDS/Neon/Cloud SQL PITR remains pending live account.",
    }
    out = ROOT / "ops" / "cert_wal_pitr.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"pass": payload["pass"], "runs": [{"ok": r["ok"], "ids": r["ids_after_pitr"]} for r in runs]}, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

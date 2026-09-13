"""Export cert Postgres dump onto the host filesystem with sha256.

The in-container named volume is NOT the recovery copy. After this script,
`backups/host/*.dump` survives `docker compose down` of the cert stack
(without deleting the host directory).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = os.environ.get("CERT_PG_CONTAINER", "aiessayassignmentchecker-postgres-1")
HOST_DIR = ROOT / "backups" / "host"


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], check=check, capture_output=True, text=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    HOST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    remote = f"/backups/host-export-{stamp}.dump"
    host_path = HOST_DIR / f"academiccheck-{stamp}.dump"

    docker("exec", "-u", "root", "-i", CONTAINER, "mkdir", "-p", "/backups")
    docker("exec", "-u", "root", "-i", CONTAINER, "chmod", "777", "/backups")
    t0 = time.perf_counter()
    docker(
        "exec",
        "-i",
        CONTAINER,
        "pg_dump",
        "-U",
        "academiccheck",
        "-d",
        "academiccheck",
        "--format=custom",
        f"--file={remote}",
    )
    dump_s = round(time.perf_counter() - t0, 3)
    docker("cp", f"{CONTAINER}:{remote}", str(host_path))
    digest = sha256_file(host_path)
    sidecar = host_path.with_suffix(host_path.suffix + ".sha256")
    sidecar.write_text(digest + "\n", encoding="utf-8")
    # Remove the in-container copy so recovery cannot cheat by reading it later.
    docker("exec", "-u", "root", "-i", CONTAINER, "rm", "-f", remote)

    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "container": CONTAINER,
        "host_path": str(host_path.relative_to(ROOT)).replace("\\", "/"),
        "size_bytes": host_path.stat().st_size,
        "sha256": digest,
        "format": "pg_dump custom",
        "dump_s": dump_s,
        "in_container_copy_deleted": True,
        "independent_of_container_lifecycle": True,
        "ok": host_path.is_file() and host_path.stat().st_size > 0,
    }
    out = ROOT / "ops" / "cert_backup_host_export.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

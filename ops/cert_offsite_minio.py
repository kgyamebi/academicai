"""MinIO (S3-compatible) offsite backup cycle. Not a live AWS/GCS account.

Uploads, downloads, checksum-matches, then proves retention prune.
Two consecutive cycles required for PASS.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops"))

from offsite_backup import (  # noqa: E402
    download_file,
    ensure_bucket,
    keys_to_delete,
    list_backup_objects,
    prune_remote,
    s3_client,
    sha256_file,
    upload_file,
)

ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://127.0.0.1:59000")
ACCESS = os.environ.get("MINIO_ROOT_USER", "academiccheck")
SECRET = os.environ.get("MINIO_ROOT_PASSWORD", "academiccheck")
BUCKET = os.environ.get("MINIO_BUCKET", "academiccheck-backups")
PREFIX = "backups/postgres/"


def wait_minio(timeout: int = 60) -> None:
    url = ENDPOINT.rstrip("/") + "/minio/health/live"
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = str(exc)
            time.sleep(1)
    raise RuntimeError(f"MinIO not ready at {url}: {last}")


def one_cycle(src: Path, expected: str, fixture: Path) -> dict:
    client = s3_client(endpoint_url=ENDPOINT, access_key=ACCESS, secret_key=SECRET)
    ensure_bucket(client, BUCKET)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    live_key = f"{PREFIX}academiccheck-{stamp}.dump"
    t0 = time.perf_counter()
    uploaded = upload_file(client, BUCKET, live_key, src)
    upload_s = round(time.perf_counter() - t0, 3)
    dest = ROOT / "backups" / "host" / f"minio-download-{stamp}.dump"
    t1 = time.perf_counter()
    downloaded = download_file(client, BUCKET, live_key, dest)
    download_s = round(time.perf_counter() - t1, 3)
    integrity = uploaded == downloaded == expected

    now = datetime.now(UTC)
    seeded = []
    for days_ago in (1, 3, 10, 20, 40, 80):
        ts = now - timedelta(days=days_ago)
        key = f"{PREFIX}academiccheck-{ts.strftime('%Y%m%dT%H%M%SZ')}.dump"
        upload_file(client, BUCKET, key, fixture)
        seeded.append(key)
    deleted = prune_remote(client, BUCKET, PREFIX, daily_keep=7, weekly_keep=4)
    remaining = [obj["key"] for obj in list_backup_objects(client, BUCKET, PREFIX)]
    old_key = f"{PREFIX}academiccheck-{(now - timedelta(days=80)).strftime('%Y%m%dT%H%M%SZ')}.dump"
    local_doomed = keys_to_delete(
        [{"key": k, "last_modified": None} for k in seeded + [live_key]],
        daily_keep=7,
        weekly_keep=4,
        now=now,
    )
    return {
        "upload_s": upload_s,
        "download_s": download_s,
        "integrity_ok": integrity,
        "old_key_was_pruned": old_key in deleted or old_key not in remaining,
        "pruned_count": len(deleted),
        "local_prune_would_delete_count": len(local_doomed),
        "ok": integrity and (old_key in deleted or old_key not in remaining),
    }


def main() -> int:
    wait_minio()
    host_meta = ROOT / "ops" / "cert_backup_host_export.json"
    fixture = ROOT / "backups" / "host" / "minio-fixture.bin"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_bytes(os.urandom(4096))
    if host_meta.is_file():
        meta = json.loads(host_meta.read_text(encoding="utf-8"))
        src = ROOT / meta["host_path"]
        expected = meta["sha256"]
        source_kind = "host_pg_dump"
    else:
        src = fixture
        expected = sha256_file(src)
        source_kind = "synthetic_fixture"

    runs = [one_cycle(src, expected, fixture), one_cycle(src, expected, fixture)]
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "emulator": "minio",
        "endpoint": ENDPOINT,
        "bucket": BUCKET,
        "source_kind": source_kind,
        "consecutive_runs": 2,
        "runs": runs,
        "live_cloud_account": False,
        "ok": all(run["ok"] for run in runs),
        "note": "Ready pending live account: set real bucket credentials. CRR not exercised.",
    }
    out = ROOT / "ops" / "cert_offsite_minio.json"
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "runs": [{"ok": r["ok"], "integrity_ok": r["integrity_ok"]} for r in runs]}, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

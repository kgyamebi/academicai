"""Application-level object storage destroy → restore → read_bytes.

Uses the same store_bytes/read_bytes path as uploads. Local disk only.
S3/CRR remains pending a live bucket.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ops"))

from verify_storage import backup_tree, inventory, restore_tree  # noqa: E402


def _one_run(workdir: Path) -> dict:
    storage = workdir / "store"
    backup = workdir / "store-backup"
    if workdir.exists():
        shutil.rmtree(workdir)
    storage.mkdir(parents=True)

    os.environ["APP_ENV"] = "test"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_PATH"] = str(storage)
    os.environ.setdefault("APP_SECRET_KEY", "dr-storage")
    os.environ.setdefault("JWT_SECRET_KEY", "dr-storage-jwt-secret-key-32bytes")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.services.documents.storage import read_bytes, store_bytes

    payloads = {
        ".txt": b"assignment body for DR read-back " * 20,
        ".pdf": b"%PDF-1.4 restored-object\n",
        ".docx": b"PK\x03\x04dr-docx",
    }
    keys = []
    expected = {}
    for ext, data in payloads.items():
        key = store_bytes(data, ext, "dr-user")
        keys.append(key)
        expected[key] = data

    before = inventory(storage)
    t0 = time.perf_counter()
    backup_tree(storage, backup)
    backup_s = round(time.perf_counter() - t0, 4)

    # Destroy: delete all objects
    shutil.rmtree(storage)
    storage.mkdir(parents=True)

    t1 = time.perf_counter()
    restore_tree(backup, storage)
    restore_s = round(time.perf_counter() - t1, 4)
    after = inventory(storage)

    get_settings.cache_clear()
    readable = {}
    for key, data in expected.items():
        readable[key] = read_bytes(key) == data

    return {
        "files": len(keys),
        "backup_s": backup_s,
        "restore_s": restore_s,
        "checksums_match": before == after,
        "app_read_bytes_ok": all(readable.values()),
        "ok": before == after and all(readable.values()),
    }


def main() -> int:
    runs = []
    for i in range(2):
        runs.append(_one_run(ROOT / "backups" / f"dr-storage-app-{i}"))
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": "local-disk",
        "app_path": "app.services.documents.storage.read_bytes",
        "s3_replication": False,
        "consecutive_runs": 2,
        "runs": runs,
        "pass": all(run["ok"] for run in runs),
        "note": "Functional app read after restore. Live object-store/CRR UNPROVEN.",
    }
    out = ROOT / "ops" / "cert_storage_app_restore.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"pass": payload["pass"], "runs": runs}, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify a Postgres logical backup artifact (gzip and optional AES-GCM envelope).

Exit: 0 OK, 1 integrity failure, 2 missing inputs.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _gunzip_ok(path: Path) -> tuple[bool, str]:
    try:
        with gzip.open(path, "rb") as fh:
            total = 0
            while True:
                chunk = fh.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
        return True, f"gzip_ok bytes={total}"
    except Exception as exc:  # noqa: BLE001
        return False, f"gzip_fail: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", required=True)
    parser.add_argument(
        "--database-url",
        default="",
        help="Optional. When set, also print tenant table counts (requires PYTHONPATH=backend).",
    )
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_backup_verification.json"))
    args = parser.parse_args()

    backup = Path(args.backup)
    report: dict = {"backup": str(backup), "ok": False, "checks": []}
    if not backup.is_file():
        report["checks"].append({"name": "exists", "ok": False, "detail": "missing"})
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2

    report["checks"].append(
        {"name": "exists", "ok": True, "detail": f"size_bytes={backup.stat().st_size}"}
    )
    report["sha256"] = _sha256_file(backup)

    work = Path(args.out).resolve().parent / "_backup_verify_work"
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "ops"))
    from backup_crypto import decrypt_file

    candidate = backup
    if backup.name.endswith(".enc"):
        key = (os.environ.get("BACKUP_ENCRYPTION_KEY") or "").strip()
        if not key:
            report["checks"].append(
                {"name": "decrypt", "ok": False, "detail": "BACKUP_ENCRYPTION_KEY missing"}
            )
            Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report, indent=2))
            return 2
        candidate = work / backup.name[: -len(".enc")]
        decrypt_file(backup, candidate, key)
        report["checks"].append({"name": "decrypt", "ok": True, "detail": str(candidate.name)})

    ok, detail = _gunzip_ok(candidate)
    report["checks"].append({"name": "gzip", "ok": ok, "detail": detail})
    if not ok:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
        sys.path.insert(0, str(ROOT / "ops"))
        from validate_restore import main as validate_main

        code = validate_main()
        report["checks"].append({"name": "database_counts", "ok": code == 0, "detail": f"exit={code}"})
        if code != 0:
            report["ok"] = False
            Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report, indent=2))
            return code
    else:
        report["checks"].append(
            {
                "name": "database_counts",
                "ok": True,
                "detail": "skipped (no --database-url); artifact-only verification",
            }
        )

    report["ok"] = all(c["ok"] for c in report["checks"])
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

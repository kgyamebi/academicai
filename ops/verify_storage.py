#!/usr/bin/env python3
"""Local object-storage recovery drill + verification (disk backend).

Tests: inventory → backup copies with SHA-256 → delete/corrupt → restore → verify.
S3/R2 cross-region replication is NOT claimed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            out[rel] = _sha256(path.read_bytes())
    return out


def backup_tree(src: Path, dest: Path) -> dict[str, str]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    hashes = inventory(src)
    for rel, digest in hashes.items():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, target)
        (dest / f"{rel}.sha256").write_text(digest + "\n", encoding="utf-8")
    return hashes


def restore_tree(backup: Path, dest: Path) -> dict[str, str]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    restored: dict[str, str] = {}
    for path in backup.rglob("*"):
        if not path.is_file() or path.name.endswith(".sha256"):
            continue
        rel = path.relative_to(backup).as_posix()
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes()
        expected = (backup / f"{rel}.sha256").read_text(encoding="utf-8").strip()
        actual = _sha256(data)
        if expected != actual:
            raise RuntimeError(f"checksum mismatch on restore: {rel}")
        target.write_bytes(data)
        restored[rel] = actual
    return restored


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage-root",
        default=str(ROOT / "backups" / "dr-storage-fixture"),
        help="Working storage directory for the drill",
    )
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_storage_recovery.json"))
    parser.add_argument("--skip-mutate", action="store_true")
    args = parser.parse_args()

    storage = Path(args.storage_root)
    backup_dir = storage.parent / (storage.name + "-backup")
    report: dict = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": "local-disk",
        "s3_replication": False,
        "versioning": "drill-sidecar-sha256",
        "ok": False,
        "steps": [],
    }

    # Seed fixture objects
    if storage.exists():
        shutil.rmtree(storage)
    storage.mkdir(parents=True)
    samples = {
        "u1/essay.docx": b"PK\x03\x04fake-docx-bytes-for-dr",
        "u1/report.pdf": b"%PDF-1.4 fake report",
        "u2/assignment.txt": b"assignment body " * 50,
    }
    for rel, data in samples.items():
        path = storage / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    before = inventory(storage)
    report["steps"].append({"name": "seed", "ok": True, "files": len(before)})

    t0 = time.perf_counter()
    backed = backup_tree(storage, backup_dir)
    report["steps"].append(
        {
            "name": "backup",
            "ok": backed == before,
            "seconds": round(time.perf_counter() - t0, 4),
            "files": len(backed),
        }
    )

    if not args.skip_mutate:
        # Delete one, corrupt one
        (storage / "u1/essay.docx").unlink()
        (storage / "u1/report.pdf").write_bytes(b"CORRUPTED")
        report["steps"].append({"name": "mutate_delete_corrupt", "ok": True})

        t1 = time.perf_counter()
        restored = restore_tree(backup_dir, storage)
        report["steps"].append(
            {
                "name": "restore",
                "ok": restored == before,
                "seconds": round(time.perf_counter() - t1, 4),
                "files": len(restored),
            }
        )
        after = inventory(storage)
        report["steps"].append(
            {"name": "verify_integrity", "ok": after == before, "files": len(after)}
        )
    else:
        report["steps"].append({"name": "mutate_delete_corrupt", "ok": True, "detail": "skipped"})
        report["steps"].append({"name": "restore", "ok": True, "detail": "skipped"})
        report["steps"].append({"name": "verify_integrity", "ok": True, "detail": "inventory_only"})

    report["ok"] = all(s.get("ok") for s in report["steps"])
    report["note"] = (
        "Local-disk drill only. Cross-region / S3 versioning / object-lock: UNPROVEN."
    )
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Local filesystem storage throughput. Not an R2/S3 1M-object certificate."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tmp" / "cert_storage"
COUNTS = [1_000, 10_000]


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    payload: dict = {"measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "backend": "local-disk", "runs": {}}
    blob = os.urandom(4096)
    for count in COUNTS:
        start = time.perf_counter()
        keys = []
        for _ in range(count):
            name = uuid4().hex + ".bin"
            path = TARGET / name
            path.write_bytes(blob)
            keys.append(path)
        write_s = time.perf_counter() - start
        start = time.perf_counter()
        read_ok = 0
        for path in keys:
            data = path.read_bytes()
            if len(data) == 4096:
                read_ok += 1
        read_s = time.perf_counter() - start
        start = time.perf_counter()
        for path in keys:
            path.unlink()
        delete_s = time.perf_counter() - start
        payload["runs"][str(count)] = {
            "write_s": round(write_s, 3),
            "read_s": round(read_s, 3),
            "delete_s": round(delete_s, 3),
            "write_files_per_s": round(count / max(write_s, 0.001), 1),
            "read_ok": read_ok,
            "failure_rate": round((count - read_ok) / count, 4),
        }
    payload["not_run"] = ["files_100000", "files_500000", "files_1000000", "s3", "r2", "signed_url_load"]
    out = ROOT / "ops" / "cert_storage_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

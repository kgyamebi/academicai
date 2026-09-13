"""MinIO (S3 API) volume cert: 100k then 1M objects of varied size. Counts are actual PUTs."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")
os.environ["STORAGE_BACKEND"] = "s3"
os.environ["S3_ENDPOINT_URL"] = os.environ.get("CERT_S3_ENDPOINT", "http://127.0.0.1:59010")
os.environ["S3_ACCESS_KEY"] = os.environ.get("CERT_S3_ACCESS_KEY", "academiccheck")
os.environ["S3_SECRET_KEY"] = os.environ.get("CERT_S3_SECRET_KEY", "academiccheck")
os.environ["S3_BUCKET"] = os.environ.get("CERT_S3_BUCKET", "academiccheck")
os.environ["S3_REGION"] = "us-east-1"

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.services.documents.storage import delete_bytes, list_keys, read_bytes, store_bytes  # noqa: E402

TIERS = [int(x) for x in os.environ.get("CERT_STORAGE_TIERS", "100000,1000000").split(",") if x.strip()]
SIZES = [1024, 4096, 16384, 65536, 131072]


def ensure_bucket() -> None:
    import boto3
    from botocore.config import Config

    settings = get_settings()
    client = boto3.client(
        "s3",
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
        config=Config(connect_timeout=5, read_timeout=30),
    )
    try:
        client.create_bucket(Bucket=settings.s3_bucket)
    except Exception as exc:
        if "BucketAlreadyOwnedByYou" not in str(exc) and "BucketAlreadyExists" not in str(exc):
            # MinIO may return 409 BucketAlreadyOwnedByYou
            if "409" not in str(exc):
                raise


def payload_for(i: int) -> bytes:
    size = SIZES[i % len(SIZES)]
    return (f"{i:08d}".encode() * ((size // 8) + 1))[:size]


def run_tier(count: int, prefix: str) -> dict:
    keys = []
    t0 = time.perf_counter()
    for i in range(count):
        blob = payload_for(i)
        key = store_bytes(blob, ".bin", f"{prefix}/{i // 10000:04d}")
        keys.append((key, len(blob)))
        if (i + 1) % 10000 == 0:
            print(f"  put {i + 1}/{count}", flush=True)
    write_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    read_ok = 0
    sample = keys[:: max(1, count // 1000)]
    for key, size in sample:
        data = read_bytes(key)
        if len(data) == size:
            read_ok += 1
    read_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    listed = list_keys(prefix, max_keys=min(10000, count))
    list_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    deleted = 0
    for key, _size in keys:
        delete_bytes(key)
        deleted += 1
    delete_s = time.perf_counter() - t0
    return {
        "count": count,
        "unique_sizes_bytes": SIZES,
        "write_s": round(write_s, 3),
        "write_files_per_s": round(count / max(write_s, 0.001), 1),
        "read_sample": len(sample),
        "read_ok": read_ok,
        "read_s": round(read_s, 3),
        "list_returned": len(listed),
        "list_s": round(list_s, 3),
        "delete_s": round(delete_s, 3),
        "deleted": deleted,
    }


def main() -> int:
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": "minio_s3_api",
        "endpoint": os.environ["S3_ENDPOINT_URL"],
        "tiers": {},
        "not_reached": [],
    }
    try:
        ensure_bucket()
    except Exception as exc:
        payload["setup_error"] = str(exc)
        payload["not_reached"] = [str(t) for t in TIERS]
        (ROOT / "ops" / "cert_storage_volume.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 1
    for count in TIERS:
        print(f"=== storage {count} objects ===", flush=True)
        try:
            payload["tiers"][str(count)] = run_tier(count, f"vol-{count}-{uuid4().hex[:6]}")
        except Exception as exc:
            payload["tiers"][str(count)] = {"error": str(exc)}
            payload["not_reached"].append({"tier": count, "reason": str(exc)})
            break
    (ROOT / "ops" / "cert_storage_volume.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"tiers": list(payload["tiers"]), "not_reached": payload["not_reached"]}, indent=2))
    return 0 if not payload["not_reached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

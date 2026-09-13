"""S3-compatible offsite backup: upload, download, integrity, retention prune.

Works against MinIO (local emulator) or a real bucket. Pointing at a live
cloud account is a configuration change only — this module is the proven path.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from botocore.config import Config

KEY_RE = re.compile(r"academiccheck-(\d{8}T\d{6}Z)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_stamp(key: str) -> datetime | None:
    name = key.rsplit("/", 1)[-1]
    match = KEY_RE.search(name)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


def keys_to_delete(
    objects: list[dict],
    *,
    daily_keep: int = 7,
    weekly_keep: int = 4,
    now: datetime | None = None,
) -> list[str]:
    """Keep last N calendar days (all objects those days) plus newest object per ISO week for M weeks."""
    now = now or datetime.now(UTC)
    dated: list[tuple[datetime, str]] = []
    for obj in objects:
        key = str(obj["key"])
        # Retention is based on the dump stamp in the object key, not S3 LastModified
        # (emulator uploads of old-named keys would otherwise never prune).
        parsed = parse_stamp(key)
        stamp = obj.get("last_modified")
        if parsed is not None:
            ts = parsed
        elif isinstance(stamp, datetime):
            ts = stamp if stamp.tzinfo else stamp.replace(tzinfo=UTC)
        else:
            continue
        dated.append((ts.astimezone(UTC), key))

    keep: set[str] = set()
    daily_cutoff = now - timedelta(days=daily_keep)
    for ts, key in dated:
        if ts >= daily_cutoff:
            keep.add(key)

    by_week: dict[tuple[int, int], list[tuple[datetime, str]]] = {}
    for ts, key in dated:
        iso = ts.isocalendar()
        by_week.setdefault((iso.year, iso.week), []).append((ts, key))
    week_cutoff = now - timedelta(weeks=weekly_keep)
    for _week, items in by_week.items():
        items.sort(key=lambda pair: pair[0], reverse=True)
        newest_ts, newest_key = items[0]
        if newest_ts >= week_cutoff:
            keep.add(newest_key)

    return sorted({key for _ts, key in dated if key not in keep})


def s3_client(*, endpoint_url: str, access_key: str, secret_key: str, region: str = "us-east-1"):
    import boto3

    kwargs = {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region_name": region or "us-east-1",
        "config": Config(
            connect_timeout=5,
            read_timeout=60,
            retries={"max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    }
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("s3", **kwargs)


def ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:
        client.create_bucket(Bucket=bucket)


def upload_file(client, bucket: str, key: str, path: Path) -> str:
    digest = sha256_file(path)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=path.read_bytes(),
        Metadata={"sha256": digest},
    )
    return digest


def download_file(client, bucket: str, key: str, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
    dest.write_bytes(body)
    return sha256_file(dest)


def list_backup_objects(client, bucket: str, prefix: str) -> list[dict]:
    out: list[dict] = []
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        resp = client.list_objects_v2(**kwargs)
        for item in resp.get("Contents") or []:
            out.append({"key": item["Key"], "last_modified": item["LastModified"], "size": item["Size"]})
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    return out


def prune_remote(client, bucket: str, prefix: str, *, daily_keep: int = 7, weekly_keep: int = 4) -> list[str]:
    objects = list_backup_objects(client, bucket, prefix)
    doomed = keys_to_delete(objects, daily_keep=daily_keep, weekly_keep=weekly_keep)
    for key in doomed:
        client.delete_object(Bucket=bucket, Key=key)
    return doomed

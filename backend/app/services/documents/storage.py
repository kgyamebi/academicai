from pathlib import Path
from uuid import uuid4

from app.config import get_settings
from app.services.ai.circuit import allow, record_failure, record_success


class StorageError(ValueError):
    pass


def store_bytes(content: bytes, extension: str, user_id: str) -> str:
    settings = get_settings()
    key = _assert_safe_key(f"{user_id}/{uuid4().hex}{extension}")
    if settings.storage_backend == "s3" and settings.s3_access_key:
        return _store_s3(content, key)
    dest = _safe_local_path(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return key


def read_bytes(storage_key: str) -> bytes:
    key = _assert_safe_key(storage_key)
    settings = get_settings()
    if settings.storage_backend == "s3" and settings.s3_access_key:
        return _read_s3(key)
    return _safe_local_path(key).read_bytes()


def delete_bytes(storage_key: str) -> None:
    key = _assert_safe_key(storage_key)
    settings = get_settings()
    if settings.storage_backend == "s3" and settings.s3_access_key:
        _delete_s3(key)
        return
    path = _safe_local_path(key)
    if path.exists():
        path.unlink()


def list_keys(prefix: str, max_keys: int = 1000) -> list[str]:
    """List object keys under a prefix. Used by volume certs; not a public API."""
    prefix = _assert_safe_key(prefix) if prefix else ""
    settings = get_settings()
    if settings.storage_backend == "s3" and settings.s3_access_key:
        return _list_s3(prefix, max_keys)
    root = Path(settings.storage_local_path).resolve()
    base = (root / prefix).resolve() if prefix else root
    if base != root and root not in base.parents and base != root:
        raise StorageError("Invalid storage key.")
    if not base.exists():
        return []
    keys: list[str] = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        keys.append(rel)
        if len(keys) >= max_keys:
            break
    return keys


def _assert_safe_key(storage_key: str) -> str:
    normalized = (storage_key or "").replace("\\", "/").lstrip("/")
    if not normalized or ".." in normalized.split("/") or ":" in normalized:
        raise StorageError("Invalid storage key.")
    return normalized


def _safe_local_path(storage_key: str) -> Path:
    normalized = _assert_safe_key(storage_key)
    root = Path(get_settings().storage_local_path).resolve()
    path = (root / normalized).resolve()
    if path != root and root not in path.parents:
        raise StorageError("Invalid storage key.")
    return path


def signed_url(storage_key: str, expires_in: int = 300) -> str:
    settings = get_settings()
    if settings.storage_backend != "s3" or not settings.s3_access_key:
        raise RuntimeError("Signed URLs require S3-compatible storage.")
    client = _s3()
    return _s3_call(
        "sign",
        lambda: client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": storage_key},
            ExpiresIn=expires_in,
        ),
    )


def _s3():
    import boto3
    from botocore.config import Config

    settings = get_settings()
    kwargs = {
        "aws_access_key_id": settings.s3_access_key,
        "aws_secret_access_key": settings.s3_secret_key,
        "region_name": settings.s3_region or "auto",
        "config": Config(
            connect_timeout=5,
            read_timeout=15,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
        kwargs["config"] = Config(
            connect_timeout=5,
            read_timeout=15,
            retries={"max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "path"},
        )
    return boto3.client("s3", **kwargs)


def _s3_call(op: str, fn):
    if not allow("s3"):
        raise StorageError("Object storage is temporarily unavailable.")
    try:
        result = fn()
        record_success("s3")
        return result
    except StorageError:
        raise
    except Exception as exc:
        record_failure("s3")
        raise StorageError(f"Object storage {op} failed.") from exc


def _store_s3(content: bytes, key: str) -> str:
    settings = get_settings()
    extra: dict = {}
    if not settings.s3_endpoint_url:
        extra["ServerSideEncryption"] = "AES256"
    _s3_call(
        "put",
        lambda: _s3().put_object(Bucket=settings.s3_bucket, Key=key, Body=content, **extra),
    )
    return key


def _read_s3(key: str) -> bytes:
    settings = get_settings()
    cap = settings.max_upload_mb * 1024 * 1024 + 1

    def _get() -> bytes:
        obj = _s3().get_object(Bucket=settings.s3_bucket, Key=key)
        return obj["Body"].read(cap)

    return _s3_call("get", _get)


def _delete_s3(key: str) -> None:
    settings = get_settings()
    _s3_call("delete", lambda: _s3().delete_object(Bucket=settings.s3_bucket, Key=key))


def _list_s3(prefix: str, max_keys: int) -> list[str]:
    settings = get_settings()

    def _page() -> list[str]:
        keys: list[str] = []
        token = None
        while len(keys) < max_keys:
            kwargs = {
                "Bucket": settings.s3_bucket,
                "Prefix": prefix,
                "MaxKeys": min(1000, max_keys - len(keys)),
            }
            if token:
                kwargs["ContinuationToken"] = token
            resp = _s3().list_objects_v2(**kwargs)
            for item in resp.get("Contents") or []:
                keys.append(item["Key"])
                if len(keys) >= max_keys:
                    break
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
            if not token:
                break
        return keys

    return _s3_call("list", _page)

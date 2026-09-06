from pathlib import Path
from uuid import uuid4

from app.config import get_settings


def store_bytes(content: bytes, extension: str, user_id: str) -> str:
    settings = get_settings()
    key = f"{user_id}/{uuid4().hex}{extension}"
    if settings.storage_backend == "s3" and settings.s3_access_key:
        return _store_s3(content, key)
    root = Path(settings.storage_local_path)
    dest = root / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return key


def read_bytes(storage_key: str) -> bytes:
    settings = get_settings()
    if settings.storage_backend == "s3" and settings.s3_access_key:
        return _read_s3(storage_key)
    path = Path(settings.storage_local_path) / storage_key
    return path.read_bytes()


def delete_bytes(storage_key: str) -> None:
    settings = get_settings()
    if settings.storage_backend == "s3" and settings.s3_access_key:
        _delete_s3(storage_key)
        return
    path = Path(settings.storage_local_path) / storage_key
    if path.exists():
        path.unlink()


def _store_s3(content: bytes, key: str) -> str:
    import httpx

    settings = get_settings()
    # Minimal S3-compatible PUT via presigned-style raw HTTP is provider-specific.
    # Keep a clear adapter hook; local storage is the default.
    raise RuntimeError(f"S3 storage adapter is configured but not fully wired for {settings.s3_bucket}/{key}")


def _read_s3(key: str) -> bytes:
    raise RuntimeError("S3 storage adapter is not fully wired in this environment.")


def _delete_s3(key: str) -> None:
    raise RuntimeError("S3 storage adapter is not fully wired in this environment.")

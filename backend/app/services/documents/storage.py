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


def signed_url(storage_key: str, expires_in: int = 300) -> str:
    settings = get_settings()
    if settings.storage_backend != "s3" or not settings.s3_access_key:
        raise RuntimeError("Signed URLs require S3-compatible storage.")
    client = _s3()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": storage_key},
        ExpiresIn=expires_in,
    )


def _s3():
    import boto3

    settings = get_settings()
    kwargs = {
        "aws_access_key_id": settings.s3_access_key,
        "aws_secret_access_key": settings.s3_secret_key,
        "region_name": settings.s3_region or "auto",
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    return boto3.client("s3", **kwargs)


def _store_s3(content: bytes, key: str) -> str:
    settings = get_settings()
    _s3().put_object(Bucket=settings.s3_bucket, Key=key, Body=content, ServerSideEncryption="AES256")
    return key


def _read_s3(key: str) -> bytes:
    settings = get_settings()
    obj = _s3().get_object(Bucket=settings.s3_bucket, Key=key)
    return obj["Body"].read()


def _delete_s3(key: str) -> None:
    settings = get_settings()
    _s3().delete_object(Bucket=settings.s3_bucket, Key=key)

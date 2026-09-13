from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

_PREFIX_V1 = "enc:v1:"
_PREFIX_V2 = "enc:v2:"
_AAD = b"academiccheck-field-v2"


def _material_to_key(raw: str) -> bytes:
    return hashlib.sha256(raw.encode("utf-8")).digest()


def _aes_keys() -> list[bytes]:
    """Current key first, then previous (grace-period decrypt)."""
    settings = get_settings()
    keys: list[bytes] = []
    current = (settings.field_encryption_key or "").strip()
    if current:
        keys.append(_material_to_key(current))
    elif settings.is_production:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is required in production.")
    previous = (settings.field_encryption_key_previous or "").strip()
    if previous and previous != current:
        keys.append(_material_to_key(previous))
    return keys


def _aes_key() -> bytes | None:
    keys = _aes_keys()
    return keys[0] if keys else None


def _fernet() -> Fernet | None:
    key = _aes_key()
    if key is None:
        return None
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_field(value: str | None) -> str:
    if not value:
        return value or ""
    if value.startswith((_PREFIX_V2, _PREFIX_V1)):
        return value
    key = _aes_key()
    if key is None:
        return value
    nonce = os.urandom(12)
    token = AESGCM(key).encrypt(nonce, value.encode("utf-8"), _AAD)
    packed = base64.urlsafe_b64encode(nonce + token).decode("ascii")
    return f"{_PREFIX_V2}{packed}"


def decrypt_field(value: str | None) -> str:
    if not value:
        return value or ""
    if value.startswith(_PREFIX_V2):
        keys = _aes_keys()
        if not keys:
            return value
        raw = base64.urlsafe_b64decode(value[len(_PREFIX_V2) :].encode("ascii"))
        nonce, token = raw[:12], raw[12:]
        for key in keys:
            try:
                return AESGCM(key).decrypt(nonce, token, _AAD).decode("utf-8")
            except Exception:  # noqa: BLE001, S112
                continue
        return value
    if value.startswith(_PREFIX_V1):
        keys = _aes_keys()
        if not keys:
            return value
        blob = value[len(_PREFIX_V1) :].encode("ascii")
        for key in keys:
            try:
                return Fernet(base64.urlsafe_b64encode(key)).decrypt(blob).decode("utf-8")
            except InvalidToken:
                continue
        return value
    return value


def reencrypt_field(value: str | None) -> str:
    """Decrypt with current-or-previous, encrypt with current. Used during rotation."""
    if not value or not value.startswith((_PREFIX_V1, _PREFIX_V2)):
        return value or ""
    plain = decrypt_field(value)
    if plain == value or not _aes_key():
        return value
    nonce = os.urandom(12)
    token = AESGCM(_aes_key()).encrypt(nonce, plain.encode("utf-8"), _AAD)
    packed = base64.urlsafe_b64encode(nonce + token).decode("ascii")
    return f"{_PREFIX_V2}{packed}"

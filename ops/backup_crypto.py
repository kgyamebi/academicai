"""AES-256-GCM envelope for logical DB dumps (at-rest backup encryption).

Format: enc:v1:<b64(nonce 12)><b64(ciphertext+tag)> written as binary:
  magic(8)=b'ACBK1\\0\\0\\0' + nonce(12) + ciphertext+tag

Key material: BACKUP_ENCRYPTION_KEY (UTF-8), stretched with SHA-256 to 32 bytes.
This is dump encryption only — not a substitute for FIELD_ENCRYPTION_KEY or TLS.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"ACBK1\0\0\0"


def _key_bytes(material: str) -> bytes:
    return hashlib.sha256(material.encode("utf-8")).digest()


def encrypt_file(src: Path, dest: Path, key_material: str) -> None:
    data = src.read_bytes()
    nonce = hashlib.sha256(data[:64] + MAGIC).digest()[:12]  # deterministic only for tests? No — random
    import os

    nonce = os.urandom(12)
    ct = AESGCM(_key_bytes(key_material)).encrypt(nonce, data, MAGIC)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(MAGIC + nonce + ct)


def decrypt_file(src: Path, dest: Path, key_material: str, previous_key_material: str = "") -> None:
    blob = src.read_bytes()
    if not blob.startswith(MAGIC):
        raise ValueError("Not an AcademicCheck encrypted backup (bad magic).")
    nonce = blob[8:20]
    ct = blob[20:]
    keys = [key_material]
    if previous_key_material and previous_key_material != key_material:
        keys.append(previous_key_material)
    last_error: Exception | None = None
    for material in keys:
        try:
            plain = AESGCM(_key_bytes(material)).decrypt(nonce, ct, MAGIC)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(plain)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise last_error or ValueError("Backup decrypt failed.")


def reencrypt_file(src: Path, dest: Path, old_key: str, new_key: str) -> None:
    tmp = dest.parent / (dest.name + ".tmpplain")
    try:
        decrypt_file(src, tmp, new_key, previous_key_material=old_key)
        encrypt_file(tmp, dest, new_key)
    finally:
        if tmp.exists():
            tmp.unlink()

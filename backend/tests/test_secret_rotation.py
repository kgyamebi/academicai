"""Application-level secret rotation with a previous-key grace period."""

from __future__ import annotations

import sys
from pathlib import Path

from app.config import get_settings
from app.core.crypto import decrypt_field, encrypt_field, reencrypt_field

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def test_field_decrypt_works_with_previous_key_during_rotation(monkeypatch):
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", "old-field-key-material-32bytes-min")
    get_settings.cache_clear()
    token = encrypt_field("student-draft")
    assert token.startswith("enc:v2:")
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", "new-field-key-material-32bytes-min")
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY_PREVIOUS", "old-field-key-material-32bytes-min")
    get_settings.cache_clear()
    assert decrypt_field(token) == "student-draft"
    rotated = reencrypt_field(token)
    assert rotated != token
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY_PREVIOUS", "")
    get_settings.cache_clear()
    assert decrypt_field(rotated) == "student-draft"
    get_settings.cache_clear()


def test_backup_decrypt_uses_previous_key(tmp_path, monkeypatch):
    from ops.backup_crypto import decrypt_file, encrypt_file, reencrypt_file

    src = tmp_path / "dump.sql"
    src.write_bytes(b"PGDUMP-BYTES")
    enc = tmp_path / "dump.sql.enc"
    encrypt_file(src, enc, "backup-old-key")
    out = tmp_path / "out.sql"
    decrypt_file(enc, out, "backup-new-key", previous_key_material="backup-old-key")
    assert out.read_bytes() == b"PGDUMP-BYTES"
    rotated = tmp_path / "dump2.sql.enc"
    reencrypt_file(enc, rotated, "backup-old-key", "backup-new-key")
    out2 = tmp_path / "out2.sql"
    decrypt_file(rotated, out2, "backup-new-key")
    assert out2.read_bytes() == b"PGDUMP-BYTES"

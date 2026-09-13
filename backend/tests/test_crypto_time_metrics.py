from datetime import UTC, datetime, timedelta

from app.core.crypto import decrypt_field, encrypt_field
from app.core.metrics import incr, snapshot
from app.core.time import as_utc, is_past, utcnow


def test_encrypt_roundtrip_when_key_absent():
    plain = "Assignment question text"
    assert decrypt_field(encrypt_field(plain)) == plain


def test_encrypt_uses_aes256_gcm_and_reads_legacy_fernet(monkeypatch):
    import base64
    import hashlib

    from cryptography.fernet import Fernet

    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", "unit-test-field-key-material")
    from app.config import get_settings

    get_settings.cache_clear()
    cipher = encrypt_field("secret assignment")
    assert cipher.startswith("enc:v2:")
    assert "secret assignment" not in cipher
    assert decrypt_field(cipher) == "secret assignment"

    key = hashlib.sha256(b"unit-test-field-key-material").digest()
    legacy = "enc:v1:" + Fernet(base64.urlsafe_b64encode(key)).encrypt(b"old rubric").decode()
    assert decrypt_field(legacy) == "old rubric"
    get_settings.cache_clear()


def test_time_helpers_treat_naive_as_utc():
    past = datetime(2020, 1, 1)
    assert as_utc(past).tzinfo == UTC
    assert is_past(past)
    assert not is_past(utcnow() + timedelta(hours=1))
    assert not is_past(None)


def test_metrics_increment():
    before = snapshot().get("test.counter", 0)
    incr("test.counter", 2)
    assert snapshot()["test.counter"] == before + 2

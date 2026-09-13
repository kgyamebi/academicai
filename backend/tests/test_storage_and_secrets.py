import pytest

from app.config import Settings
from app.services.documents.storage import StorageError, delete_bytes, read_bytes, store_bytes


def test_local_storage_roundtrip_and_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path))
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    from app.config import get_settings

    get_settings.cache_clear()
    key = store_bytes(b"draft-bytes", ".txt", "user-1")
    assert read_bytes(key) == b"draft-bytes"
    with pytest.raises(StorageError):
        read_bytes("../secret.txt")
    with pytest.raises(StorageError):
        read_bytes("..\\windows\\system.ini")
    delete_bytes("/etc/passwd")
    assert not (tmp_path / "etc" / "passwd").exists()
    delete_bytes(key)
    get_settings.cache_clear()


def test_production_rejects_default_secrets():
    settings = Settings.model_construct(
        app_env="production",
        jwt_secret_key="change-me-jwt",
        app_secret_key="change-me",
        field_encryption_key="",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        settings.assert_deployable_secrets()


def test_production_accepts_strong_secrets():
    settings = Settings.model_construct(
        app_env="production",
        jwt_secret_key="production-jwt-secret-key-32b-min",
        app_secret_key="production-app-secret",
        field_encryption_key="field-key-for-fernet-material",
    )
    settings.assert_deployable_secrets()


def test_non_production_allows_local_defaults():
    Settings.model_construct(app_env="test", jwt_secret_key="short").assert_deployable_secrets()


def test_application_source_has_no_live_provider_secrets():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    forbidden = (b"sk_live_", b"whsec_", b"AKIA")
    for path in root.rglob("*.py"):
        if path.name in {"firewall.py", "logging.py"}:
            continue
        data = path.read_bytes()
        for needle in forbidden:
            assert needle not in data, f"{path} contains {needle!r}"


def test_secrets_file_injects_allowed_keys(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.core.secrets import inject_secrets_file, reset_secrets_injection

    path = tmp_path / "secrets.json"
    path.write_text('{"JWT_SECRET_KEY": "injected-jwt-secret-key-32bytesmin"}', encoding="utf-8")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("SECRETS_FILE", str(path))
    reset_secrets_injection()
    get_settings.cache_clear()
    inject_secrets_file()
    get_settings.cache_clear()
    assert get_settings().jwt_secret_key == "injected-jwt-secret-key-32bytesmin"
    get_settings.cache_clear()
    reset_secrets_injection()


def test_secrets_file_missing_fails_closed(monkeypatch):
    from app.core.secrets import inject_secrets_file, reset_secrets_injection

    monkeypatch.setenv("SECRETS_FILE", "/nonexistent/academiccheck-secrets.json")
    reset_secrets_injection()
    with pytest.raises(RuntimeError, match="does not exist"):
        inject_secrets_file()
    reset_secrets_injection()


def test_jwt_previous_secret_verifies_during_rotation(monkeypatch):
    from app.config import get_settings
    from app.core.security import create_token, decode_token

    monkeypatch.setenv("JWT_SECRET_KEY", "current-secret-key-32-bytes-minxx")
    monkeypatch.delenv("JWT_SECRET_PREVIOUS", raising=False)
    get_settings.cache_clear()
    token = create_token("user-rotate", "access")
    monkeypatch.setenv("JWT_SECRET_KEY", "rotated-secret-key-32-bytes-minxx")
    monkeypatch.setenv("JWT_SECRET_PREVIOUS", "current-secret-key-32-bytes-minxx")
    get_settings.cache_clear()
    payload = decode_token(token)
    assert payload["sub"] == "user-rotate"
    get_settings.cache_clear()


def test_unsafe_doi_is_not_fetched(monkeypatch):
    from app.services.analysis.verify_sources import verify_reference

    def boom(*_args, **_kwargs):
        raise AssertionError("unsafe DOI must not be fetched")

    monkeypatch.setattr("app.services.analysis.verify_sources._crossref_doi", boom)
    result = verify_reference(doi="https://169.254.169.254/latest/meta-data")
    assert result.status == "could_not_verify"
    assert result.provider == "none"

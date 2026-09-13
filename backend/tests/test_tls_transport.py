"""Local TLS proof: HSTS in production mode + TLS 1.2+ context (self-signed)."""

from __future__ import annotations

import ssl
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.config import get_settings
from app.core.tls import server_ssl_context


def _dev_cert(folder: Path) -> tuple[Path, Path]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(minutes=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    cert_path = folder / "dev.crt"
    key_path = folder / "dev.key"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


def test_hsts_set_in_production(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "production")
    response = client.get("/api/live")
    assert response.headers.get("Strict-Transport-Security", "").startswith("max-age=")
    csp = response.headers.get("Content-Security-Policy") or ""
    assert "default-src 'none'" in csp


def test_tls_context_rejects_tls1():
    with tempfile.TemporaryDirectory() as tmp:
        cert, key = _dev_cert(Path(tmp))
        ctx = server_ssl_context(str(cert), str(key))
        assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2
        assert ssl.TLSVersion.TLSv1 not in (ctx.minimum_version,)
        assert ctx.minimum_version.value >= ssl.TLSVersion.TLSv1_2.value

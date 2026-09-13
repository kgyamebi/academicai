"""Local TLS 1.2+ handshake against a self-signed in-process server. Not SSL Labs."""

from __future__ import annotations

import json
import socket
import ssl
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]


def _cert(folder: Path) -> tuple[str, str]:
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
    return str(cert_path), str(key_path)


def main() -> int:
    import sys

    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.tls import server_ssl_context

    with tempfile.TemporaryDirectory() as tmp:
        cert, key = _cert(Path(tmp))
        ctx = server_ssl_context(cert, key)
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        ready = threading.Event()

        def _serve() -> None:
            ready.set()
            conn, _ = srv.accept()
            try:
                tls = ctx.wrap_socket(conn, server_side=True)
                tls.sendall(b"HTTP/1.1 200 OK\r\nStrict-Transport-Security: max-age=63072000\r\nContent-Length: 2\r\n\r\nOK")
                tls.close()
            finally:
                srv.close()

        threading.Thread(target=_serve, daemon=True).start()
        ready.wait(2)
        client_ctx = ssl.create_default_context()
        client_ctx.check_hostname = False
        client_ctx.verify_mode = ssl.CERT_NONE
        client_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        with socket.create_connection(("127.0.0.1", port), timeout=3) as raw:
            with client_ctx.wrap_socket(raw, server_hostname="localhost") as tls:
                version = tls.version()
                cipher = tls.cipher()
                tls.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                body = tls.recv(1024).decode("utf-8", errors="replace")
        payload = {
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ok": version in {"TLSv1.2", "TLSv1.3"} and "Strict-Transport-Security" in body,
            "tls_version": version,
            "cipher": cipher[0] if cipher else None,
            "hsts_header_present": "Strict-Transport-Security" in body,
            "minimum_tls": "TLSv1.2",
            "ssl_labs_production_domain": False,
            "note": "Self-signed local handshake. Production certificate/infra still needs SSL Labs / live domain.",
        }
    out = ROOT / "ops" / "cert_tls_local.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

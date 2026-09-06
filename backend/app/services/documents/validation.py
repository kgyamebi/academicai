import io
import zipfile
from dataclasses import dataclass

from app.config import get_settings

ALLOWED = {
    ".pdf": {"application/pdf", "application/x-pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
}

SIGNATURES = {
    ".pdf": (b"%PDF",),
    ".docx": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
}


class DocumentSecurityError(ValueError):
    pass


@dataclass
class ValidatedUpload:
    extension: str
    mime_type: str
    size_bytes: int
    signature_hex: str


def _ext(filename: str) -> str:
    name = (filename or "").lower().strip()
    if "." not in name:
        raise DocumentSecurityError("File must have an extension.")
    return "." + name.rsplit(".", 1)[-1]


def validate_upload(filename: str, content: bytes, declared_mime: str | None = None) -> ValidatedUpload:
    settings = get_settings()
    extension = _ext(filename)
    if extension not in ALLOWED:
        raise DocumentSecurityError(
            "This file type is not supported yet. Upload a PDF, DOCX, TXT, or Markdown file."
        )
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise DocumentSecurityError(f"File is too large. Maximum size is {settings.max_upload_mb} MB.")
    if len(content) == 0:
        raise DocumentSecurityError("The uploaded file is empty.")

    mime = (declared_mime or "").split(";")[0].strip().lower() or "application/octet-stream"
    if mime not in ALLOWED[extension] and mime != "application/octet-stream":
        # Extension + signature still decide trust; MIME is a warning, not sole authority.
        if extension in {".txt", ".md"} and mime.startswith("text/"):
            pass
        else:
            raise DocumentSecurityError("The file type did not match its contents. Please upload a valid document.")

    sigs = SIGNATURES.get(extension)
    if sigs and not any(content.startswith(sig) for sig in sigs):
        raise DocumentSecurityError("The file signature does not match a valid document. The upload was rejected.")

    if extension == ".docx":
        _assert_safe_zip(content)
    if extension == ".pdf":
        if content.count(b"/Encrypt") > 40:
            raise DocumentSecurityError("This PDF appears malformed and was rejected.")

    _scan_clamav(content)

    return ValidatedUpload(
        extension=extension,
        mime_type=mime,
        size_bytes=len(content),
        signature_hex=content[:8].hex(),
    )


def _assert_safe_zip(content: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            if len(zf.infolist()) > 2000:
                raise DocumentSecurityError("This document contains too many internal files and was rejected.")
            uncompressed = 0
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or ".." in name.split("/"):
                    raise DocumentSecurityError("The document contained an unsafe path and was rejected.")
                uncompressed += info.file_size
                if info.file_size > 80 * 1024 * 1024:
                    raise DocumentSecurityError("A file inside the document is too large.")
                if info.compress_size and info.file_size / max(info.compress_size, 1) > 200:
                    raise DocumentSecurityError("The document looks like a compressed bomb and was rejected.")
            if uncompressed > 200 * 1024 * 1024:
                raise DocumentSecurityError("Uncompressed document size exceeds safety limits.")
    except zipfile.BadZipFile as exc:
        raise DocumentSecurityError("The Word document could not be opened safely.") from exc


def _scan_clamav(content: bytes) -> None:
    host = get_settings().clamav_host
    if not host:
        return
    import socket

    hostname, _, port = host.partition(":")
    try:
        with socket.create_connection((hostname, int(port or 3310)), timeout=8) as sock:
            sock.sendall(b"zINSTREAM\0")
            offset = 0
            chunk = 8192
            while offset < len(content):
                part = content[offset : offset + chunk]
                sock.sendall(len(part).to_bytes(4, "big") + part)
                offset += chunk
            sock.sendall((0).to_bytes(4, "big"))
            verdict = sock.recv(4096).decode("utf-8", errors="replace")
    except OSError as exc:
        if get_settings().is_production:
            raise DocumentSecurityError("Virus scanning is unavailable. Upload rejected.") from exc
        return
    if "FOUND" in verdict:
        raise DocumentSecurityError("The file failed a malware scan and was rejected.")

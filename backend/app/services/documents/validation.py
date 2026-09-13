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

_DANGEROUS_STEMS = {
    "exe",
    "bat",
    "cmd",
    "com",
    "pif",
    "scr",
    "js",
    "jse",
    "vbs",
    "vbe",
    "ps1",
    "msi",
    "dll",
    "jar",
    "sh",
    "html",
    "htm",
    "wsf",
    "cpl",
}

_DOCX_FORBIDDEN = (
    "vbaproject",
    "vbadata",
    "oleobject",
    "word/embeddings/",
    "word/macrosheets/",
    "word/activex/",
)

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
    raw = filename or ""
    if "\x00" in raw:
        raise DocumentSecurityError("The file name is not allowed.")
    name = raw.lower().strip().replace("\\", "/")
    if "/" in name or name.startswith("."):
        raise DocumentSecurityError("The file name is not allowed.")
    if "." not in name:
        raise DocumentSecurityError("File must have an extension.")
    parts = [p for p in name.split(".") if p]
    if len(parts) < 2:
        raise DocumentSecurityError("File must have an extension.")
    for stem in parts[1:-1]:
        if stem in _DANGEROUS_STEMS:
            raise DocumentSecurityError("This filename is not allowed.")
    return "." + parts[-1]


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
        _assert_safe_pdf(content)

    from app.services.documents.malware import MalwareRejected, quarantine_scan_release

    try:
        quarantine_scan_release(content, suffix=extension)
    except MalwareRejected as exc:
        raise DocumentSecurityError(str(exc)) from exc

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
                name = info.filename.replace("\\", "/").lower()
                if name.startswith("/") or ".." in name.split("/"):
                    raise DocumentSecurityError("The document contained an unsafe path and was rejected.")
                if any(forbidden in name for forbidden in _DOCX_FORBIDDEN):
                    raise DocumentSecurityError("Documents with macros or embedded objects are not allowed.")
                uncompressed += info.file_size
                if info.file_size > 80 * 1024 * 1024:
                    raise DocumentSecurityError("A file inside the document is too large.")
                if info.compress_size and info.file_size / max(info.compress_size, 1) > 200:
                    raise DocumentSecurityError("The document looks like a compressed bomb and was rejected.")
            if uncompressed > 200 * 1024 * 1024:
                raise DocumentSecurityError("Uncompressed document size exceeds safety limits.")
    except zipfile.BadZipFile as exc:
        raise DocumentSecurityError("The Word document could not be opened safely.") from exc


def _assert_safe_pdf(content: bytes) -> None:
    if content.count(b"/Encrypt") > 40:
        raise DocumentSecurityError("This PDF appears malformed and was rejected.")
    lowered = content.lower()
    if b"/javascript" in lowered or b"/launch" in lowered or b"/richmedia" in lowered:
        raise DocumentSecurityError("This PDF contains active content and was rejected.")
    if content.count(b"/EmbeddedFile") > 8:
        raise DocumentSecurityError("This PDF contains too many embedded files and was rejected.")

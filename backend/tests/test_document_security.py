import pytest

from app.services.documents.validation import DocumentSecurityError, validate_upload


def test_rejects_unknown_extension():
    with pytest.raises(DocumentSecurityError):
        validate_upload("malware.exe", b"MZ", "application/octet-stream")


def test_rejects_pdf_with_wrong_signature():
    with pytest.raises(DocumentSecurityError):
        validate_upload("essay.pdf", b"not-a-pdf", "application/pdf")


def test_accepts_plain_text():
    result = validate_upload("draft.txt", b"This is a long enough assignment draft for testing.", "text/plain")
    assert result.extension == ".txt"


def test_rejects_dangerous_double_extension():
    with pytest.raises(DocumentSecurityError):
        validate_upload("malware.exe.pdf", b"%PDF-1.4\n%", "application/pdf")


def test_accepts_harmless_multi_dot_name():
    result = validate_upload("my.draft.txt", b"This is a long enough assignment draft for testing.", "text/plain")
    assert result.extension == ".txt"


def test_rejects_pdf_with_javascript():
    with pytest.raises(DocumentSecurityError):
        validate_upload("essay.pdf", b"%PDF-1.4\n/JavaScript (app.alert(1))\n", "application/pdf")


def test_rejects_docx_with_macro_part():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("word/vbaProject.bin", b"macro")
    with pytest.raises(DocumentSecurityError):
        validate_upload(
            "essay.docx",
            buf.getvalue(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

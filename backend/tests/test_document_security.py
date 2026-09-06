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

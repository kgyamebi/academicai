from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.crypto import decrypt_field, encrypt_field
from app.core.logging import get_logger
from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.deps import get_current_user, owned_assignment, owned_document
from app.models.document import Document, DocumentAsset
from app.models.user import User
from app.schemas.common import PasteDocumentIn
from app.services.documents.extract_job import (
    HEAVY_EXTRACT_EXTENSIONS,
    attach_version,
    persist_extraction,
    process_extract_job,
)
from app.services.documents.extractor import extract_document
from app.services.documents.storage import delete_bytes, store_bytes
from app.services.documents.validation import DocumentSecurityError, validate_upload
from app.workers.queue import enqueue_extract

log = get_logger("documents")

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _serialize(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "filename": doc.original_filename,
        "status": doc.status,
        "word_count": doc.word_count,
        "word_count_excl_references": doc.word_count_excl_references,
        "paragraph_count": doc.paragraph_count,
        "sentence_count": doc.sentence_count,
        "page_count": doc.page_count,
        "language": doc.language,
        "assignment_id": str(doc.assignment_id) if doc.assignment_id else None,
        "excerpt": decrypt_field(doc.normalized_text or "")[:400],
        "extraction_error": doc.extraction_error,
    }


@router.post("/upload")
async def upload_document(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    assignment_id: UUID | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "upload", user)
    content = await _read_capped(file)
    try:
        validated = validate_upload(file.filename or "upload.bin", content, file.content_type)
    except DocumentSecurityError as exc:
        raise HTTPException(400, str(exc)) from exc
    if assignment_id:
        owned_assignment(assignment_id, user, db)
    heavy = validated.extension in HEAVY_EXTRACT_EXTENSIONS
    extracted = None
    if not heavy:
        try:
            extracted = extract_document(content, validated.extension)
        except DocumentSecurityError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            log.error("document_extract_failed", error=str(exc))
            raise HTTPException(400, "We could not read this document. Try a PDF, DOCX, TXT, or Markdown file.") from exc
    key = store_bytes(content, validated.extension, str(user.id))
    expires = None
    if user.is_guest:
        expires = datetime.now(UTC) + timedelta(hours=get_settings().guest_retention_hours)
    document = Document(
        user_id=user.id,
        assignment_id=assignment_id,
        filename=key.split("/")[-1],
        original_filename=file.filename or "upload",
        mime_type=validated.mime_type,
        extension=validated.extension,
        file_signature=validated.signature_hex,
        size_bytes=validated.size_bytes,
        storage_key=key,
        status="queued" if heavy else "extracted",
        extracted_text="",
        normalized_text="",
        expires_at=expires,
    )
    try:
        db.add(document)
        db.flush()
        db.add(
            DocumentAsset(
                document_id=document.id,
                kind="original",
                storage_key=key,
                mime_type=validated.mime_type,
                size_bytes=validated.size_bytes,
            )
        )
        if extracted is not None:
            persist_extraction(db, document, extracted)
        if assignment_id:
            attach_version(db, assignment_id, document.id)
        db.commit()
    except Exception:
        db.rollback()
        try:
            delete_bytes(key)
        except Exception as exc:  # noqa: BLE001
            log.warning("storage_compensate_failed", key=key, error=str(exc))
        raise
    db.refresh(document)
    if heavy:
        queued = enqueue_extract(str(document.id))
        if not queued:
            settings = get_settings()
            if settings.is_production or settings.require_queue:
                document.status = "failed"
                document.extraction_error = "Document workers are unavailable. Please try again shortly."
                db.commit()
                raise HTTPException(503, "Document workers are unavailable. Please try again shortly.")
            background.add_task(process_extract_job, str(document.id))
    return _serialize(document)


@router.post("/paste")
def paste_document(
    payload: PasteDocumentIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "upload", user)
    content = payload.text.encode("utf-8")
    try:
        validated = validate_upload(payload.filename if payload.filename.endswith(".txt") else "draft.txt", content, "text/plain")
        extracted = extract_document(content, ".txt")
    except DocumentSecurityError as exc:
        raise HTTPException(400, str(exc)) from exc
    if payload.assignment_id:
        owned_assignment(payload.assignment_id, user, db)
    key = store_bytes(content, ".txt", str(user.id))
    expires = datetime.now(UTC) + timedelta(hours=get_settings().guest_retention_hours) if user.is_guest else None
    document = Document(
        user_id=user.id,
        assignment_id=payload.assignment_id,
        filename=key.split("/")[-1],
        original_filename=payload.filename,
        mime_type="text/plain",
        extension=".txt",
        file_signature=validated.signature_hex,
        size_bytes=len(content),
        storage_key=key,
        status="extracted",
        extracted_text=encrypt_field(extracted.text),
        normalized_text=encrypt_field(extracted.normalized_text),
        word_count=extracted.word_count,
        word_count_excl_references=extracted.word_count_excl_references,
        word_count_excl_headings=extracted.word_count_excl_headings,
        paragraph_count=extracted.paragraph_count,
        sentence_count=extracted.sentence_count,
        page_count=1,
        language=extracted.language,
        expires_at=expires,
    )
    db.add(document)
    db.flush()
    persist_extraction(db, document, extracted)
    if payload.assignment_id:
        attach_version(db, payload.assignment_id, document.id)
    db.commit()
    db.refresh(document)
    return _serialize(document)


@router.get("/{document_id}")
def get_document(document_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = owned_document(document_id, user, db)
    data = _serialize(document)
    data["paragraphs"] = [
        {"id": str(p.id), "index": p.index, "text": decrypt_field(p.text), "is_heading": p.is_heading}
        for p in sorted(document.paragraphs, key=lambda x: x.index)
    ]
    return data


async def _read_capped(file: UploadFile) -> bytes:
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    declared = file.size
    if declared is not None and declared > max_bytes:
        raise HTTPException(400, f"File is too large. Maximum size is {get_settings().max_upload_mb} MB.")
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(400, f"File is too large. Maximum size is {get_settings().max_upload_mb} MB.")
        chunks.append(chunk)
    return b"".join(chunks)

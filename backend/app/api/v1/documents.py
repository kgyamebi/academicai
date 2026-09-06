from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.deps import get_current_user, owned_assignment, owned_document
from app.models.assignment import AssignmentVersion
from app.models.document import Document, DocumentAsset, DocumentParagraph, DocumentSection
from app.models.user import User
from app.schemas.common import PasteDocumentIn
from app.services.documents.extractor import extract_document
from app.services.documents.storage import store_bytes
from app.services.documents.validation import DocumentSecurityError, validate_upload

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
        "excerpt": (doc.normalized_text or "")[:400],
    }


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    assignment_id: UUID | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "upload", user)
    content = await file.read()
    try:
        validated = validate_upload(file.filename or "upload.bin", content, file.content_type)
        extracted = extract_document(content, validated.extension)
    except DocumentSecurityError as exc:
        raise HTTPException(400, str(exc)) from exc
    if assignment_id:
        owned_assignment(assignment_id, user, db)
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
        status="extracted",
        extracted_text=extracted.text,
        normalized_text=extracted.normalized_text,
        word_count=extracted.word_count,
        word_count_excl_references=extracted.word_count_excl_references,
        word_count_excl_headings=extracted.word_count_excl_headings,
        paragraph_count=extracted.paragraph_count,
        sentence_count=extracted.sentence_count,
        page_count=extracted.page_count,
        language=extracted.language,
        expires_at=expires,
    )
    db.add(document)
    db.flush()
    db.add(DocumentAsset(document_id=document.id, kind="original", storage_key=key, mime_type=validated.mime_type, size_bytes=validated.size_bytes))
    _store_structure(db, document.id, extracted)
    if assignment_id:
        _attach_version(db, assignment_id, document.id)
    db.commit()
    db.refresh(document)
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
        extracted_text=extracted.text,
        normalized_text=extracted.normalized_text,
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
    _store_structure(db, document.id, extracted)
    if payload.assignment_id:
        _attach_version(db, payload.assignment_id, document.id)
    db.commit()
    db.refresh(document)
    return _serialize(document)


@router.get("/{document_id}")
def get_document(document_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = owned_document(document_id, user, db)
    data = _serialize(document)
    data["paragraphs"] = [
        {"id": str(p.id), "index": p.index, "text": p.text, "is_heading": p.is_heading}
        for p in sorted(document.paragraphs, key=lambda x: x.index)
    ]
    return data


def _store_structure(db: Session, document_id, extracted) -> None:
    for p in extracted.paragraphs:
        db.add(
            DocumentParagraph(
                document_id=document_id,
                index=p.index,
                text=p.text,
                heading_level=p.heading_level,
                is_heading=p.is_heading,
                char_start=p.char_start,
                char_end=p.char_end,
                word_count=p.word_count,
            )
        )
    for s in extracted.sections:
        db.add(
            DocumentSection(
                document_id=document_id,
                heading=s.heading,
                section_type=s.section_type,
                start_paragraph=s.start_paragraph,
                end_paragraph=s.end_paragraph,
                sort_order=s.sort_order,
            )
        )


def _attach_version(db: Session, assignment_id, document_id) -> None:
    existing = db.query(AssignmentVersion).filter(AssignmentVersion.assignment_id == assignment_id).all()
    for v in existing:
        v.is_current = False
    db.add(
        AssignmentVersion(
            assignment_id=assignment_id,
            document_id=document_id,
            name=f"Draft {len(existing) + 1}",
            version_number=len(existing) + 1,
            is_current=True,
        )
    )

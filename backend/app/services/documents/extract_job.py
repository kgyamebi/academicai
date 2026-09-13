"""Background PDF/DOCX extraction. The upload handler must not call this inline."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.crypto import encrypt_field
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.assignment import AssignmentVersion
from app.models.document import Document, DocumentParagraph, DocumentSection
from app.services.documents.extractor import ExtractedDocument, extract_document
from app.services.documents.storage import read_bytes
from app.services.documents.validation import DocumentSecurityError

log = get_logger("documents.extract")

HEAVY_EXTRACT_EXTENSIONS = {".pdf", ".docx"}


def persist_extraction(db: Session, document: Document, extracted: ExtractedDocument) -> None:
    document.extracted_text = encrypt_field(extracted.text)
    document.normalized_text = encrypt_field(extracted.normalized_text)
    document.word_count = extracted.word_count
    document.word_count_excl_references = extracted.word_count_excl_references
    document.word_count_excl_headings = extracted.word_count_excl_headings
    document.paragraph_count = extracted.paragraph_count
    document.sentence_count = extracted.sentence_count
    document.page_count = extracted.page_count
    document.language = extracted.language
    document.extraction_error = None
    document.status = "extracted"
    db.add_all(
        [
            DocumentParagraph(
                document_id=document.id,
                index=p.index,
                text=encrypt_field(p.text),
                heading_level=p.heading_level,
                is_heading=p.is_heading,
                char_start=p.char_start,
                char_end=p.char_end,
                word_count=p.word_count,
            )
            for p in extracted.paragraphs
        ]
    )
    db.add_all(
        [
            DocumentSection(
                document_id=document.id,
                heading=s.heading,
                section_type=s.section_type,
                start_paragraph=s.start_paragraph,
                end_paragraph=s.end_paragraph,
                sort_order=s.sort_order,
            )
            for s in extracted.sections
        ]
    )


def process_extract_job(document_id: str) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, UUID(document_id))
        if not document:
            log.warning("extract_job_missing_document", document_id=document_id)
            return
        if document.status == "extracted":
            return
        document.status = "extracting"
        db.commit()
        content = read_bytes(document.storage_key)
        extracted = extract_document(content, document.extension)
        persist_extraction(db, document, extracted)
        db.commit()
    except DocumentSecurityError as exc:
        _fail(db, document_id, str(exc))
    except Exception as exc:  # noqa: BLE001
        log.error("extract_job_failed", document_id=document_id, error=str(exc), exc_info=exc)
        _fail(db, document_id, "We could not read this document. Try a PDF, DOCX, TXT, or Markdown file.")
    finally:
        db.close()


def _fail(db: Session, document_id: str, message: str) -> None:
    try:
        document = db.get(Document, UUID(document_id))
        if not document:
            return
        document.status = "failed"
        document.extraction_error = message
        db.commit()
    except Exception as exc:  # noqa: BLE001
        log.error("extract_job_mark_failed", document_id=document_id, error=str(exc), exc_info=exc)


def attach_version(db: Session, assignment_id, document_id) -> None:
    existing = db.query(AssignmentVersion).filter(AssignmentVersion.assignment_id == assignment_id).all()
    for version in existing:
        version.is_current = False
    db.add(
        AssignmentVersion(
            assignment_id=assignment_id,
            document_id=document_id,
            name=f"Draft {len(existing) + 1}",
            version_number=len(existing) + 1,
            is_current=True,
        )
    )

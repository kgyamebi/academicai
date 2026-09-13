from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.metrics import incr
from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.deps import get_current_user, owned_document
from app.models.admin import AnalyticsEvent
from app.models.citation import Citation, Reference, SourceVerification
from app.models.user import User
from app.schemas.common import CitationVerifyIn
from app.services.analysis.verify_sources import verify_reference
from app.services.security_events import record_security_event

router = APIRouter(prefix="/api/citations", tags=["citations"])

_DISCLAIMER = (
    "Inability to verify a reference is not proof that it is fabricated. "
    "Citation verification may not find every legitimate source. "
    "AcademicCheck never invents a replacement source."
)


@router.get("")
def list_citations(
    document_id: UUID = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = owned_document(document_id, user, db)
    citations = list(
        db.scalars(select(Citation).where(Citation.document_id == document.id).order_by(Citation.char_start).limit(200))
    )
    references = list(
        db.scalars(
            select(Reference).where(Reference.document_id == document.id).order_by(Reference.sort_order).limit(200)
        )
    )
    latest = _latest_verifications(db, [r.id for r in references])
    incr("citations.listed")
    return {
        "document_id": str(document.id),
        "disclaimer": _DISCLAIMER,
        "citations": [
            {
                "id": str(c.id),
                "raw_text": c.raw_text,
                "author": c.author,
                "year": c.year,
                "style_guess": c.style_guess,
            }
            for c in citations
        ],
        "references": [_reference_payload(r, latest.get(r.id)) for r in references],
    }


@router.post("/verify")
def verify_citation(
    payload: CitationVerifyIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "citation", user)
    reference = db.get(Reference, payload.reference_id)
    if not reference:
        raise HTTPException(404, "Reference not found.")
    owned_document(reference.document_id, user, db)
    result = verify_reference(title=reference.title or "", doi=reference.doi or "", year=reference.year or "")
    row = SourceVerification(
        reference_id=reference.id,
        status=result.status,
        confidence=result.confidence,
        explanation=result.explanation,
        provider=result.provider,
    )
    db.add(row)
    db.add(
        AnalyticsEvent(
            user_id=user.id,
            event_name="citation_check_used",
            path="/api/citations/verify",
            properties=str({"status": result.status, "provider": result.provider})[:2000],
        )
    )
    record_security_event(
        db,
        "citation_verify",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=result.status,
    )
    db.commit()
    incr("citations.verified")
    return {
        "reference_id": str(reference.id),
        "status": result.status,
        "confidence": result.confidence,
        "explanation": result.explanation,
        "provider": result.provider,
        "matched_title": result.matched_title,
        "disclaimer": _DISCLAIMER,
    }


def _latest_verifications(db: Session, reference_ids: list) -> dict:
    if not reference_ids:
        return {}
    newest = (
        select(
            SourceVerification.reference_id.label("reference_id"),
            func.max(SourceVerification.created_at).label("max_created"),
        )
        .where(SourceVerification.reference_id.in_(reference_ids))
        .group_by(SourceVerification.reference_id)
        .subquery()
    )
    rows = db.scalars(
        select(SourceVerification).join(
            newest,
            (SourceVerification.reference_id == newest.c.reference_id)
            & (SourceVerification.created_at == newest.c.max_created),
        )
    ).all()
    latest: dict = {}
    for row in rows:
        latest.setdefault(row.reference_id, row)
    return latest


def _reference_payload(reference: Reference, latest: SourceVerification | None) -> dict:
    return {
        "id": str(reference.id),
        "raw_text": reference.raw_text,
        "author": reference.author,
        "year": reference.year,
        "title": reference.title,
        "doi": reference.doi,
        "missing_fields": reference.missing_fields,
        "verification": (
            {
                "status": latest.status,
                "confidence": latest.confidence,
                "explanation": latest.explanation,
                "provider": latest.provider,
            }
            if latest
            else None
        ),
    }

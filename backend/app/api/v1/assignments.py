from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, owned_assignment
from app.models.analysis import AnalysisJob, AnalysisReport
from app.models.assignment import Assignment, AssignmentQuestion, AssignmentVersion, Rubric, RubricCriterion
from app.models.user import User
from app.schemas.common import AssignmentCreateIn, AssignmentUpdateIn, VersionIn
from app.services.analysis.question import analyze_question

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


def _serialize(assignment: Assignment) -> dict:
    return {
        "id": str(assignment.id),
        "title": assignment.title,
        "academic_level": assignment.academic_level,
        "citation_style": assignment.citation_style,
        "discipline": assignment.discipline,
        "notes": assignment.notes,
        "status": assignment.status,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "question": assignment.question.raw_text if assignment.question else "",
        "question_analysis": json.loads(assignment.question.analysis_json)
        if assignment.question and assignment.question.analysis_json
        else {},
        "rubric": {
            "raw_text": assignment.rubric.raw_text,
            "criteria": [
                {"id": str(c.id), "name": c.name, "weight_percent": c.weight_percent, "max_points": c.max_points}
                for c in assignment.rubric.criteria
            ],
        }
        if assignment.rubric
        else None,
        "versions": [
            {
                "id": str(v.id),
                "name": v.name,
                "version_number": v.version_number,
                "is_current": v.is_current,
                "document_id": str(v.document_id) if v.document_id else None,
            }
            for v in assignment.versions
            if not v.deleted_at
        ],
    }


@router.get("")
def list_assignments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(Assignment).where(Assignment.user_id == user.id, Assignment.deleted_at.is_(None))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(
        q.order_by(Assignment.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": [_serialize(a) for a in items], "total": total, "page": page, "page_size": page_size}


@router.post("")
def create_assignment(payload: AssignmentCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assignment = Assignment(
        user_id=user.id,
        title=payload.title,
        academic_level=payload.academic_level,
        citation_style=payload.citation_style,
        discipline=payload.discipline,
        target_word_count=payload.target_word_count,
        notes=payload.notes,
    )
    db.add(assignment)
    db.flush()
    if payload.question.strip():
        parsed = analyze_question(payload.question, payload.academic_level)
        db.add(
            AssignmentQuestion(
                assignment_id=assignment.id,
                raw_text=payload.question,
                command_words=", ".join(parsed.command_words),
                topic=parsed.topic,
                scope=parsed.scope,
                required_concepts=", ".join(parsed.required),
                interpretation=parsed.interpretation,
                analysis_json=json.dumps(parsed.to_dict()),
            )
        )
    if payload.rubric_text or payload.rubric_criteria:
        _save_rubric(db, assignment.id, payload.rubric_text, payload.rubric_criteria)
    db.commit()
    db.refresh(assignment)
    return _serialize(assignment)


@router.get("/{assignment_id}")
def get_assignment(assignment_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assignment = owned_assignment(assignment_id, user, db)
    latest = db.scalar(
        select(AnalysisReport)
        .join(AnalysisJob, AnalysisJob.id == AnalysisReport.job_id)
        .where(AnalysisReport.assignment_id == assignment.id)
        .order_by(AnalysisReport.created_at.desc())
    )
    data = _serialize(assignment)
    data["latest_report_id"] = str(latest.id) if latest else None
    data["latest_score"] = latest.overall_score if latest else None
    return data


@router.put("/{assignment_id}")
def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = owned_assignment(assignment_id, user, db)
    if payload.title is not None:
        assignment.title = payload.title
    if payload.academic_level is not None:
        assignment.academic_level = payload.academic_level
    if payload.citation_style is not None:
        assignment.citation_style = payload.citation_style
    if payload.notes is not None:
        assignment.notes = payload.notes
    if payload.question is not None:
        parsed = analyze_question(payload.question, assignment.academic_level)
        if assignment.question:
            assignment.question.raw_text = payload.question
            assignment.question.command_words = ", ".join(parsed.command_words)
            assignment.question.topic = parsed.topic
            assignment.question.scope = parsed.scope
            assignment.question.interpretation = parsed.interpretation
            assignment.question.analysis_json = json.dumps(parsed.to_dict())
        else:
            db.add(
                AssignmentQuestion(
                    assignment_id=assignment.id,
                    raw_text=payload.question,
                    command_words=", ".join(parsed.command_words),
                    topic=parsed.topic,
                    interpretation=parsed.interpretation,
                    analysis_json=json.dumps(parsed.to_dict()),
                )
            )
    if payload.rubric_text is not None or payload.rubric_criteria is not None:
        _save_rubric(db, assignment.id, payload.rubric_text or "", payload.rubric_criteria or [])
    db.commit()
    db.refresh(assignment)
    return _serialize(assignment)


@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import UTC, datetime

    assignment = owned_assignment(assignment_id, user, db)
    assignment.deleted_at = datetime.now(UTC)
    db.commit()
    return {"ok": True}


@router.post("/{assignment_id}/versions")
def create_version(
    assignment_id: UUID,
    payload: VersionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = owned_assignment(assignment_id, user, db)
    current_max = max((v.version_number for v in assignment.versions), default=0)
    for v in assignment.versions:
        v.is_current = False
    version = AssignmentVersion(
        assignment_id=assignment.id,
        document_id=payload.document_id,
        name=payload.name,
        version_number=current_max + 1,
        is_current=True,
        notes=payload.notes,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return {"id": str(version.id), "name": version.name, "version_number": version.version_number}


@router.delete("/{assignment_id}/versions/{version_id}")
def delete_version(
    assignment_id: UUID,
    version_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import UTC, datetime

    assignment = owned_assignment(assignment_id, user, db)
    version = next((v for v in assignment.versions if v.id == version_id), None)
    if not version:
        raise HTTPException(404, "Version not found.")
    version.deleted_at = datetime.now(UTC)
    db.commit()
    return {"ok": True}


def _save_rubric(db: Session, assignment_id: UUID, raw_text: str, criteria: list[dict]) -> None:
    assignment = db.get(Assignment, assignment_id)
    rubric = assignment.rubric if assignment else None
    if not rubric:
        rubric = Rubric(assignment_id=assignment_id, raw_text=raw_text or "")
        db.add(rubric)
        db.flush()
    rubric.raw_text = raw_text or rubric.raw_text
    for existing in list(rubric.criteria):
        db.delete(existing)
    parsed = criteria or _parse_rubric_text(raw_text)
    for i, item in enumerate(parsed):
        db.add(
            RubricCriterion(
                rubric_id=rubric.id,
                name=str(item.get("name") or f"Criterion {i+1}"),
                description=str(item.get("description") or ""),
                weight_percent=int(item.get("weight_percent") or 0),
                max_points=int(item.get("max_points") or item.get("weight_percent") or 0),
                sort_order=i,
            )
        )


def _parse_rubric_text(raw: str) -> list[dict]:
    rows = []
    for line in (raw or "").splitlines():
        if "—" in line or "-" in line:
            parts = line.replace("—", "-").split("-", 1)
            name = parts[0].strip()
            rest = parts[1] if len(parts) > 1 else ""
            digits = "".join(ch for ch in rest if ch.isdigit())
            weight = int(digits) if digits else 0
            if name:
                rows.append({"name": name, "weight_percent": weight, "max_points": weight})
    return rows

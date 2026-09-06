from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admin import SecurityEvent


def record_security_event(
    db: Session,
    event_type: str,
    *,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: str = "",
    severity: str = "info",
) -> None:
    db.add(
        SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details[:2000],
            severity=severity,
        )
    )

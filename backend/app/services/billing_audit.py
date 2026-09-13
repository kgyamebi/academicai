"""Append-only hash-chained financial audit trail."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.billing import FinancialAuditEntry

GENESIS = "0" * 64


def append_audit(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    payload: dict | None = None,
) -> FinancialAuditEntry:
    payload_hash = hashlib.sha256(
        json.dumps(payload or {}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    last = db.scalar(select(FinancialAuditEntry).order_by(FinancialAuditEntry.created_at.desc(), FinancialAuditEntry.id.desc()))
    prev = last.entry_hash if last else GENESIS
    entry_hash = hashlib.sha256(f"{prev}|{event_type}|{entity_type}|{entity_id}|{payload_hash}".encode()).hexdigest()
    row = FinancialAuditEntry(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        payload_hash=payload_hash,
        prev_hash=prev,
        entry_hash=entry_hash,
    )
    db.add(row)
    db.flush()
    return row


def verify_chain(db: Session) -> bool:
    rows = list(db.scalars(select(FinancialAuditEntry).order_by(FinancialAuditEntry.created_at.asc(), FinancialAuditEntry.id.asc())))
    prev = GENESIS
    for row in rows:
        expected = hashlib.sha256(
            f"{prev}|{row.event_type}|{row.entity_type}|{row.entity_id}|{row.payload_hash}".encode()
        ).hexdigest()
        if row.prev_hash != prev or row.entry_hash != expected:
            return False
        prev = row.entry_hash
    return True


def install_append_only_guards(db: Session) -> None:
    """SQLite/Postgres triggers: reject UPDATE/DELETE on historical audit rows."""
    dialect = db.bind.dialect.name if db.bind is not None else "sqlite"
    if dialect == "sqlite":
        db.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS financial_audit_no_update
                BEFORE UPDATE ON financial_audit_entries
                BEGIN
                    SELECT RAISE(ABORT, 'financial audit is append-only');
                END;
                """
            )
        )
        db.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS financial_audit_no_delete
                BEFORE DELETE ON financial_audit_entries
                BEGIN
                    SELECT RAISE(ABORT, 'financial audit is append-only');
                END;
                """
            )
        )
        return
    db.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION financial_audit_immutable() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'financial audit is append-only';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    db.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_update ON financial_audit_entries"))
    db.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_delete ON financial_audit_entries"))
    db.execute(
        text(
            """
            CREATE TRIGGER financial_audit_no_update
            BEFORE UPDATE ON financial_audit_entries
            FOR EACH ROW EXECUTE FUNCTION financial_audit_immutable();
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TRIGGER financial_audit_no_delete
            BEFORE DELETE ON financial_audit_entries
            FOR EACH ROW EXECUTE FUNCTION financial_audit_immutable();
            """
        )
    )

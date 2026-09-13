"""Keyset (cursor) pagination helpers.

Shallow OFFSET is allowed for the first pages so existing clients keep working.
Anything deeper is rejected so the API cannot execute a multi-second OFFSET scan.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, or_

# Rows skipped via OFFSET before the API refuses and requires a cursor.
# 200 = ten pages at page_size 20, or five pages at page_size 40.
MAX_OFFSET_ROWS = 200
DEEP_OFFSET_MESSAGE = (
    "Offset pagination is limited to the first pages. "
    "Use cursor-based pagination (pass the next_cursor from the previous response) "
    "instead of a deep page number."
)


def enforce_shallow_offset(page: int, page_size: int) -> None:
    """Reject OFFSET depth that would walk tens of thousands of rows."""
    offset = max(0, (page - 1) * page_size)
    if offset >= MAX_OFFSET_ROWS:
        raise HTTPException(400, DEEP_OFFSET_MESSAGE)


def encode_cursor(ts: datetime, row_id: UUID) -> str:
    payload = json.dumps({"t": ts.isoformat(), "id": str(row_id)}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(raw: str) -> tuple[datetime, UUID]:
    text = (raw or "").strip()
    if not text:
        raise HTTPException(400, "Invalid list cursor.")
    padded = text + "=" * (-len(text) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        ts = datetime.fromisoformat(str(data["t"]))
        row_id = UUID(str(data["id"]))
    except (KeyError, ValueError, json.JSONDecodeError, OSError) as exc:
        raise HTTPException(400, "Invalid list cursor.") from exc
    return ts, row_id


def keyset_before(ts_col, id_col, ts: datetime, row_id: UUID):
    """Rows strictly before (ts, id) for DESC (updated_at, id) order."""
    return or_(ts_col < ts, and_(ts_col == ts, id_col < row_id))


def keyset_after(ts_col, id_col, ts: datetime, row_id: UUID):
    """Rows strictly after (ts, id) for ASC (created_at, id) order."""
    return or_(ts_col > ts, and_(ts_col == ts, id_col > row_id))


def next_cursor_from(items: list, *, page_size: int, ts_attr: str = "updated_at") -> str | None:
    if len(items) < page_size or not items:
        return None
    last = items[-1]
    ts = getattr(last, ts_attr)
    if ts is None:
        return None
    return encode_cursor(ts, last.id)

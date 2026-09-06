"""Print tenant-table counts. Use before and after a restore drill.

Exit 2 if the database is unreachable. This does not invent a successful restore.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("UNPROVEN: DATABASE_URL is not set")
        return 2
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        print(f"UNPROVEN: database unreachable ({exc})")
        return 2
    from app.models.analysis import AnalysisJob, AnalysisReport
    from app.models.assignment import Assignment
    from app.models.billing import Credit, Payment, Subscription
    from app.models.document import Document

    with Session(engine) as db:
        rows = {
            "assignments": db.scalar(select(func.count(Assignment.id))) or 0,
            "documents": db.scalar(select(func.count(Document.id))) or 0,
            "reports": db.scalar(select(func.count(AnalysisReport.id))) or 0,
            "jobs": db.scalar(select(func.count(AnalysisJob.id))) or 0,
            "credits": db.scalar(select(func.count(Credit.id))) or 0,
            "payments": db.scalar(select(func.count(Payment.id))) or 0,
            "subscriptions": db.scalar(select(func.count(Subscription.id))) or 0,
        }
    for key, value in rows.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

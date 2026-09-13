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

    if os.environ.get("VALIDATE_RELATIONSHIPS", "1") == "1" and not url.startswith("sqlite"):
        orphans = {}
        with engine.connect() as conn:
            checks = {
                "documents_missing_user": "SELECT COUNT(*) FROM documents d LEFT JOIN users u ON d.user_id = u.id WHERE u.id IS NULL",
                "assignments_missing_user": "SELECT COUNT(*) FROM assignments a LEFT JOIN users u ON a.user_id = u.id WHERE u.id IS NULL",
                "reports_missing_job": "SELECT COUNT(*) FROM analysis_reports r LEFT JOIN analysis_jobs j ON r.job_id = j.id WHERE j.id IS NULL",
                "payments_missing_user": "SELECT COUNT(*) FROM payments p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL",
            }
            for name, sql in checks.items():
                orphans[name] = int(conn.execute(text(sql)).scalar() or 0)
                print(f"orphan_{name}={orphans[name]}")
        if any(orphans.values()):
            print("FAIL: relationship orphans after restore")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

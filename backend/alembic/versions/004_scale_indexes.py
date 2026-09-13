"""composite indexes for job and finding lists

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "analysis_jobs" in tables:
        names = {idx["name"] for idx in inspector.get_indexes("analysis_jobs")}
        if "ix_analysis_jobs_user_status" not in names:
            op.create_index("ix_analysis_jobs_user_status", "analysis_jobs", ["user_id", "status"])
    if "analysis_findings" in tables:
        names = {idx["name"] for idx in inspector.get_indexes("analysis_findings")}
        if "ix_analysis_findings_report_severity" not in names:
            op.create_index(
                "ix_analysis_findings_report_severity",
                "analysis_findings",
                ["report_id", "severity"],
            )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "analysis_findings" in tables:
        names = {idx["name"] for idx in inspector.get_indexes("analysis_findings")}
        if "ix_analysis_findings_report_severity" in names:
            op.drop_index("ix_analysis_findings_report_severity", table_name="analysis_findings")
    if "analysis_jobs" in tables:
        names = {idx["name"] for idx in inspector.get_indexes("analysis_jobs")}
        if "ix_analysis_jobs_user_status" in names:
            op.drop_index("ix_analysis_jobs_user_status", table_name="analysis_jobs")

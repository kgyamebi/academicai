"""indexes for stale-job reaper

Revision ID: 007
Revises: 006
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_index(inspector, table: str, name: str, columns: list[str]) -> None:
    if table not in set(inspector.get_table_names()):
        return
    names = {idx["name"] for idx in inspector.get_indexes(table)}
    if name in names:
        return
    op.create_index(name, table, columns)


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    _ensure_index(inspector, "analysis_jobs", "ix_analysis_jobs_status_started", ["status", "started_at"])
    _ensure_index(inspector, "analysis_jobs", "ix_analysis_jobs_status_created", ["status", "created_at"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "analysis_jobs" not in tables:
        return
    names = {idx["name"] for idx in inspector.get_indexes("analysis_jobs")}
    for name in ("ix_analysis_jobs_status_created", "ix_analysis_jobs_status_started"):
        if name in names:
            op.drop_index(name, table_name="analysis_jobs")

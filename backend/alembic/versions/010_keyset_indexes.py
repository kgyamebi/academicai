"""keyset pagination indexes (user/updated/id, findings created/id)

Revision ID: 010
Revises: 009_mfa_job_heartbeat
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect, text

revision: str = "010"
down_revision: Union[str, None] = "009_mfa_job_heartbeat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_index(inspector, table: str, name: str, columns: list[str], *, where: str | None = None) -> None:
    if table not in set(inspector.get_table_names()):
        return
    names = {idx["name"] for idx in inspector.get_indexes(table)}
    if name in names:
        return
    if where:
        op.create_index(name, table, columns, postgresql_where=text(where), sqlite_where=text(where))
    else:
        op.create_index(name, table, columns)


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    _ensure_index(
        inspector,
        "assignments",
        "ix_assignments_user_updated_id",
        ["user_id", "updated_at", "id"],
        where="deleted_at IS NULL",
    )
    _ensure_index(
        inspector,
        "documents",
        "ix_documents_user_created_id",
        ["user_id", "created_at", "id"],
        where="deleted_at IS NULL",
    )
    _ensure_index(
        inspector,
        "analysis_findings",
        "ix_analysis_findings_report_created_id",
        ["report_id", "created_at", "id"],
    )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    for table, name in (
        ("analysis_findings", "ix_analysis_findings_report_created_id"),
        ("documents", "ix_documents_user_created_id"),
        ("assignments", "ix_assignments_user_updated_id"),
    ):
        if table in tables and name in {idx["name"] for idx in inspector.get_indexes(table)}:
            op.drop_index(name, table_name=table)

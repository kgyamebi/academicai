"""production hardening columns and indexes

Revision ID: 002
Revises: 001
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {col["name"] for col in inspect(op.get_bind()).get_columns(table)}


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _indexes(table: str) -> set[str]:
    return {idx["name"] for idx in inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    users = _columns("users")
    if "failed_login_count" not in users:
        op.add_column("users", sa.Column("failed_login_count", sa.Integer(), server_default="0", nullable=False))
    if "locked_until" not in users:
        op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    reports = _columns("analysis_reports")
    if "share_password_hash" not in reports:
        op.add_column("analysis_reports", sa.Column("share_password_hash", sa.String(255), nullable=True))
    if "share_expires_at" not in reports:
        op.add_column("analysis_reports", sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=True))
    if "share_view_count" not in reports:
        op.add_column("analysis_reports", sa.Column("share_view_count", sa.Integer(), server_default="0", nullable=False))

    existing_tables = _tables()
    if "share_access_logs" not in existing_tables:
        op.create_table(
            "share_access_logs",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("report_id", sa.Uuid(), sa.ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False),
            sa.Column("action", sa.String(32), nullable=False),
            sa.Column("success", sa.Boolean(), nullable=False),
            sa.Column("ip_address", sa.String(64), nullable=True),
            sa.Column("user_agent", sa.String(512), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "webhook_events" not in existing_tables:
        op.create_table(
            "webhook_events",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("provider", sa.String(32), nullable=False),
            sa.Column("event_id", sa.String(255), nullable=False),
            sa.Column("event_type", sa.String(120), nullable=False),
            sa.Column("payload_hash", sa.String(64), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("event_id", name="uq_webhook_events_event_id"),
        )

    def add_index(name: str, table: str, cols: list[str]) -> None:
        if name not in _indexes(table):
            op.create_index(name, table, cols)

    add_index("ix_analysis_jobs_user_status_created", "analysis_jobs", ["user_id", "status", "created_at"])
    add_index("ix_assignments_user_created", "assignments", ["user_id", "created_at"])
    add_index("ix_documents_user_assignment", "documents", ["user_id", "assignment_id"])
    add_index("ix_payments_user_status", "payments", ["user_id", "status"])
    add_index("ix_credit_tx_job_status", "credit_transactions", ["analysis_job_id", "status"])


def downgrade() -> None:
    for name, table in (
        ("ix_credit_tx_job_status", "credit_transactions"),
        ("ix_payments_user_status", "payments"),
        ("ix_documents_user_assignment", "documents"),
        ("ix_assignments_user_created", "assignments"),
        ("ix_analysis_jobs_user_status_created", "analysis_jobs"),
    ):
        if name in _indexes(table):
            op.drop_index(name, table_name=table)
    if "webhook_events" in _tables():
        op.drop_table("webhook_events")
    if "share_access_logs" in _tables():
        op.drop_table("share_access_logs")
    reports = _columns("analysis_reports")
    for col in ("share_view_count", "share_expires_at", "share_password_hash"):
        if col in reports:
            op.drop_column("analysis_reports", col)
    users = _columns("users")
    for col in ("locked_until", "failed_login_count"):
        if col in users:
            op.drop_column("users", col)

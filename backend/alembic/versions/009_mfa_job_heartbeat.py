"""Alembic: MFA columns + analysis job heartbeat/recovery."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "009_mfa_job_heartbeat"
down_revision = "008"
branch_labels = None
depends_on = None


def _has_column(inspector, table: str, column: str) -> bool:
    if table not in set(inspector.get_table_names()):
        return False
    return column in {c["name"] for c in inspector.get_columns(table)}


def _has_index(inspector, table: str, name: str) -> bool:
    if table not in set(inspector.get_table_names()):
        return False
    return name in {i["name"] for i in inspector.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "users" in set(inspector.get_table_names()):
        if not _has_column(inspector, "users", "mfa_secret_encrypted"):
            op.add_column("users", sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True))
        if not _has_column(inspector, "users", "mfa_enabled"):
            op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), server_default="false", nullable=False))
        if not _has_column(inspector, "users", "mfa_backup_codes_hash"):
            op.add_column("users", sa.Column("mfa_backup_codes_hash", sa.Text(), nullable=True))
        if not _has_column(inspector, "users", "mfa_confirmed_at"):
            op.add_column("users", sa.Column("mfa_confirmed_at", sa.DateTime(timezone=True), nullable=True))
    if "analysis_jobs" in set(inspector.get_table_names()):
        if not _has_column(inspector, "analysis_jobs", "heartbeat_at"):
            op.add_column("analysis_jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_column(inspector, "analysis_jobs", "recovery_count"):
            op.add_column(
                "analysis_jobs", sa.Column("recovery_count", sa.Integer(), server_default="0", nullable=False)
            )
        if not _has_index(inspector, "analysis_jobs", "ix_analysis_jobs_heartbeat_at"):
            op.create_index("ix_analysis_jobs_heartbeat_at", "analysis_jobs", ["heartbeat_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _has_index(inspector, "analysis_jobs", "ix_analysis_jobs_heartbeat_at"):
        op.drop_index("ix_analysis_jobs_heartbeat_at", table_name="analysis_jobs")
    if _has_column(inspector, "analysis_jobs", "recovery_count"):
        op.drop_column("analysis_jobs", "recovery_count")
    if _has_column(inspector, "analysis_jobs", "heartbeat_at"):
        op.drop_column("analysis_jobs", "heartbeat_at")
    if _has_column(inspector, "users", "mfa_confirmed_at"):
        op.drop_column("users", "mfa_confirmed_at")
    if _has_column(inspector, "users", "mfa_backup_codes_hash"):
        op.drop_column("users", "mfa_backup_codes_hash")
    if _has_column(inspector, "users", "mfa_enabled"):
        op.drop_column("users", "mfa_enabled")
    if _has_column(inspector, "users", "mfa_secret_encrypted"):
        op.drop_column("users", "mfa_secret_encrypted")

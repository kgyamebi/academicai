"""Alembic: email verification lifecycle columns.

Revision ID: 013
Revises: 012
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table: str, column: str) -> bool:
    if table not in set(inspector.get_table_names()):
        return False
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "users" not in set(inspector.get_table_names()):
        return
    if not _has_column(inspector, "users", "verification_sent_at"):
        op.add_column("users", sa.Column("verification_sent_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column(inspector, "users", "pending_email"):
        op.add_column("users", sa.Column("pending_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "users" not in set(inspector.get_table_names()):
        return
    if _has_column(inspector, "users", "pending_email"):
        op.drop_column("users", "pending_email")
    if _has_column(inspector, "users", "verification_sent_at"):
        op.drop_column("users", "verification_sent_at")

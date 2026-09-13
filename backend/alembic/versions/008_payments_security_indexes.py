"""indexes for payment list + security event time

Revision ID: 008
Revises: 007
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "008"
down_revision: Union[str, None] = "007"
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
    _ensure_index(inspector, "payments", "ix_payments_user_created", ["user_id", "created_at"])
    _ensure_index(inspector, "security_events", "ix_security_events_created", ["created_at"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    for table, name in (
        ("payments", "ix_payments_user_created"),
        ("security_events", "ix_security_events_created"),
    ):
        if table not in set(inspector.get_table_names()):
            continue
        names = {idx["name"] for idx in inspector.get_indexes(table)}
        if name in names:
            op.drop_index(name, table_name=table)

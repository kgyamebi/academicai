"""composite index for latest source verification lookup

Revision ID: 011
Revises: 010
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "011"
down_revision: Union[str, None] = "010"
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
    _ensure_index(
        inspector,
        "source_verifications",
        "ix_source_verifications_reference_created",
        ["reference_id", "created_at"],
    )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    if "source_verifications" not in set(inspector.get_table_names()):
        return
    names = {idx["name"] for idx in inspector.get_indexes("source_verifications")}
    if "ix_source_verifications_reference_created" in names:
        op.drop_index("ix_source_verifications_reference_created", table_name="source_verifications")

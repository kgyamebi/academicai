"""composite indexes for citation, reference, and analytics list paths

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "006"
down_revision: Union[str, None] = "005"
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
    _ensure_index(inspector, "citations", "ix_citations_document_id_pk", ["document_id", "id"])
    _ensure_index(inspector, "references", "ix_references_document_sort", ["document_id", "sort_order"])
    _ensure_index(inspector, "analytics_events", "ix_analytics_events_user_event", ["user_id", "event_name"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    for table, name in (
        ("analytics_events", "ix_analytics_events_user_event"),
        ("references", "ix_references_document_sort"),
        ("citations", "ix_citations_document_id_pk"),
    ):
        if table in tables and name in {idx["name"] for idx in inspector.get_indexes(table)}:
            op.drop_index(name, table_name=table)

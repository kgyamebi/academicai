"""Alembic: dunning columns, pending plan, financial audit trail.

Revision ID: 012
Revises: 011
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table: str, column: str) -> bool:
    if table not in set(inspector.get_table_names()):
        return False
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "subscriptions" in set(inspector.get_table_names()):
        if not _has_column(inspector, "subscriptions", "dunning_attempts"):
            op.add_column(
                "subscriptions",
                sa.Column("dunning_attempts", sa.Integer(), server_default="0", nullable=False),
            )
        if not _has_column(inspector, "subscriptions", "pending_plan_id"):
            op.add_column("subscriptions", sa.Column("pending_plan_id", sa.Uuid(), nullable=True))
        if not _has_column(inspector, "subscriptions", "disputed_at"):
            op.add_column("subscriptions", sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True))
        inspector = inspect(bind)
        fks = {fk["name"] for fk in inspector.get_foreign_keys("subscriptions")}
        if "fk_subscriptions_pending_plan_id" not in fks and _has_column(inspector, "subscriptions", "pending_plan_id"):
            op.create_foreign_key(
                "fk_subscriptions_pending_plan_id",
                "subscriptions",
                "plans",
                ["pending_plan_id"],
                ["id"],
            )

    inspector = inspect(bind)
    if "financial_audit_entries" not in set(inspector.get_table_names()):
        op.create_table(
            "financial_audit_entries",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("event_type", sa.String(64), nullable=False),
            sa.Column("entity_type", sa.String(32), nullable=False),
            sa.Column("entity_id", sa.String(64), nullable=False),
            sa.Column("payload_hash", sa.String(64), nullable=False, server_default=""),
            sa.Column("prev_hash", sa.String(64), nullable=False, server_default=""),
            sa.Column("entry_hash", sa.String(64), nullable=False),
        )
        op.create_index("ix_financial_audit_entries_event_type", "financial_audit_entries", ["event_type"])
        op.create_index("ix_financial_audit_entries_entity_id", "financial_audit_entries", ["entity_id"])
        op.create_index("ix_financial_audit_entries_entry_hash", "financial_audit_entries", ["entry_hash"], unique=True)

    dialect = bind.dialect.name
    if dialect == "postgresql":
        bind.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION financial_audit_immutable() RETURNS trigger AS $$
                BEGIN
                    RAISE EXCEPTION 'financial audit is append-only';
                END;
                $$ LANGUAGE plpgsql;
                """
            )
        )
        bind.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_update ON financial_audit_entries"))
        bind.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_delete ON financial_audit_entries"))
        bind.execute(
            text(
                """
                CREATE TRIGGER financial_audit_no_update
                BEFORE UPDATE ON financial_audit_entries
                FOR EACH ROW EXECUTE FUNCTION financial_audit_immutable();
                """
            )
        )
        bind.execute(
            text(
                """
                CREATE TRIGGER financial_audit_no_delete
                BEFORE DELETE ON financial_audit_entries
                FOR EACH ROW EXECUTE FUNCTION financial_audit_immutable();
                """
            )
        )
    elif dialect == "sqlite":
        bind.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS financial_audit_no_update
                BEFORE UPDATE ON financial_audit_entries
                BEGIN
                    SELECT RAISE(ABORT, 'financial audit is append-only');
                END;
                """
            )
        )
        bind.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS financial_audit_no_delete
                BEFORE DELETE ON financial_audit_entries
                BEGIN
                    SELECT RAISE(ABORT, 'financial audit is append-only');
                END;
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = bind.dialect.name
    if "financial_audit_entries" in set(inspector.get_table_names()):
        if dialect == "postgresql":
            bind.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_update ON financial_audit_entries"))
            bind.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_delete ON financial_audit_entries"))
            bind.execute(text("DROP FUNCTION IF EXISTS financial_audit_immutable()"))
        elif dialect == "sqlite":
            bind.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_update"))
            bind.execute(text("DROP TRIGGER IF EXISTS financial_audit_no_delete"))
        op.drop_table("financial_audit_entries")
    inspector = inspect(bind)
    if "subscriptions" in set(inspector.get_table_names()):
        fks = {fk["name"] for fk in inspector.get_foreign_keys("subscriptions")}
        if "fk_subscriptions_pending_plan_id" in fks:
            op.drop_constraint("fk_subscriptions_pending_plan_id", "subscriptions", type_="foreignkey")
        if _has_column(inspector, "subscriptions", "disputed_at"):
            op.drop_column("subscriptions", "disputed_at")
        if _has_column(inspector, "subscriptions", "pending_plan_id"):
            op.drop_column("subscriptions", "pending_plan_id")
        if _has_column(inspector, "subscriptions", "dunning_attempts"):
            op.drop_column("subscriptions", "dunning_attempts")

"""Add last_quality_success_time and drop has_ever_worked from ace_quality_cache; add password_changed_at to user.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-14

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence
else:
    Sequence = object

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_quality_cache_table_name() -> str | None:
    """Return the current quality cache table name, or None if neither exists."""
    bind = op.get_bind()
    existing_tables = {
        row[0] for row in bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    }
    if "ace_quality_cache" in existing_tables:
        return "ace_quality_cache"
    if "quality_cache" in existing_tables:
        return "quality_cache"
    return None


def upgrade() -> None:
    bind = op.get_bind()

    table_name = _get_quality_cache_table_name()
    if table_name:
        existing_columns = {row[1] for row in bind.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()}
        needs_add = "last_quality_success_time" not in existing_columns
        needs_drop = "has_ever_worked" in existing_columns
        if needs_add or needs_drop:
            with op.batch_alter_table(table_name) as batch_op:
                if needs_add:
                    batch_op.add_column(sa.Column("last_quality_success_time", sa.DateTime(), nullable=True))
                if needs_drop:
                    batch_op.drop_column("has_ever_worked")

    user_columns = {row[1] for row in bind.execute(sa.text("PRAGMA table_info(user)")).fetchall()}
    if "password_changed_at" not in user_columns:
        with op.batch_alter_table("user") as batch_op:
            batch_op.add_column(sa.Column("password_changed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()

    table_name = _get_quality_cache_table_name()
    if table_name:
        existing_columns = {row[1] for row in bind.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()}
        needs_add = "has_ever_worked" not in existing_columns
        needs_drop = "last_quality_success_time" in existing_columns
        if needs_add or needs_drop:
            with op.batch_alter_table(table_name) as batch_op:
                if needs_add:
                    batch_op.add_column(sa.Column("has_ever_worked", sa.Boolean(), nullable=False, server_default="0"))
                if needs_drop:
                    batch_op.drop_column("last_quality_success_time")

    user_columns = {row[1] for row in bind.execute(sa.text("PRAGMA table_info(user)")).fetchall()}
    if "password_changed_at" in user_columns:
        with op.batch_alter_table("user") as batch_op:
            batch_op.drop_column("password_changed_at")

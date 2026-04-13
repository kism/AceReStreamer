"""Add persistent content_id to xc_id mapping table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-09

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence
else:
    Sequence = object

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    # Check if table already exists (idempotent)
    tables_query = sa.text("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in bind.execute(tables_query).fetchall()}
    if "content_id_xc_id" in existing_tables:
        return

    op.create_table(
        "content_id_xc_id",
        sa.Column("xc_id", sa.Integer(), primary_key=True),
        sa.Column("content_id", sa.String(40), nullable=False),
    )
    op.create_index("ix_content_id_xc_id_content_id", "content_id_xc_id", ["content_id"], unique=True)

    # Seed from existing ace_streams to preserve current IDs
    if "ace_streams" in existing_tables:
        bind.execute(sa.text("INSERT INTO content_id_xc_id (xc_id, content_id) SELECT id, content_id FROM ace_streams"))


def downgrade() -> None:
    op.drop_index("ix_content_id_xc_id_content_id", table_name="content_id_xc_id")
    op.drop_table("content_id_xc_id")

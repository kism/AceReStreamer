"""Add iptv_streams and xc_stream_map tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-20

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

    existing_tables = {
        row[0] for row in bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    }

    if "iptv_streams" not in existing_tables:
        op.create_table(
            "iptv_streams",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(255), nullable=False, server_default=""),
            sa.Column("upstream_url", sa.String(2048), nullable=False),
            sa.Column("slug", sa.String(16), nullable=False),
            sa.Column("source_name", sa.String(255), nullable=False),
            sa.Column("tvg_id", sa.String(100), nullable=False, server_default=""),
            sa.Column("tvg_logo", sa.String(255), nullable=True),
            sa.Column("group_title", sa.String(100), nullable=False, server_default=""),
            sa.Column("last_scraped_time", sa.DateTime, nullable=True),
        )
        op.create_index("ix_iptv_streams_id", "iptv_streams", ["id"])
        op.create_index("ix_iptv_streams_slug", "iptv_streams", ["slug"], unique=True)

    if "xc_stream_map" not in existing_tables:
        op.create_table(
            "xc_stream_map",
            sa.Column("xc_id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("stream_type", sa.String(10), nullable=False),
            sa.Column("stream_key", sa.String(64), nullable=False),
        )
        op.create_index("ix_xc_stream_map_xc_id", "xc_stream_map", ["xc_id"])
        op.create_index(
            "uq_xc_stream_map_type_key",
            "xc_stream_map",
            ["stream_type", "stream_key"],
            unique=True,
        )

        # Pre-populate from ace_streams to preserve backward compatibility.
        # Existing ace streams keep their current id values as xc_ids.
        if "ace_streams" in existing_tables:
            bind.execute(
                sa.text(
                    "INSERT INTO xc_stream_map (xc_id, stream_type, stream_key) "
                    "SELECT id, 'ace', content_id FROM ace_streams"
                )
            )


def downgrade() -> None:
    bind = op.get_bind()

    existing_tables = {
        row[0] for row in bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    }

    if "xc_stream_map" in existing_tables:
        op.drop_table("xc_stream_map")

    if "iptv_streams" in existing_tables:
        op.drop_table("iptv_streams")

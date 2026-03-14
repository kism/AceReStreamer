"""Drop legacy tables.

Revision ID: 0001
Revises:
Create Date: 2026-03-14

"""


from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence
else:
    Sequence = object

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LEGACY_TABLES = ["acequalitycache", "contentidinfohash", "content_id_infohash", "content_id_xc_id"]


def upgrade() -> None:
    for table in _LEGACY_TABLES:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))


def downgrade() -> None:
    pass

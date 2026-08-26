"""Drop the user table, users/auth were removed in 1.3.0.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-08

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence
else:
    Sequence = object

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text('DROP TABLE IF EXISTS "user"'))


def downgrade() -> None:
    pass

"""Programmatic Alembic migration runner."""

from pathlib import Path
from typing import TYPE_CHECKING

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext

if TYPE_CHECKING:
    from sqlalchemy import Engine
else:
    Engine = object

MIGRATION_DIR = Path(__file__).parent


def _make_config(engine: Engine) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATION_DIR))
    cfg.attributes["engine"] = engine
    return cfg


def get_current_revision(engine: Engine) -> str | None:
    """Return the current Alembic revision for the given engine, or None if untracked."""
    with engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def upgrade(engine: Engine, target: str = "head") -> None:
    """Upgrade the database to the given revision (default: head)."""
    command.upgrade(_make_config(engine), target)


def downgrade(engine: Engine, target: str) -> None:
    """Downgrade the database to the given revision."""
    command.downgrade(_make_config(engine), target)

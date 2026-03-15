"""Programmatic Alembic migration runner, bypassing env.py."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlmodel import SQLModel

# Import all models so SQLModel.metadata is fully populated
import acere.database.models
import acere.database.models.user  # noqa: F401

if TYPE_CHECKING:
    from sqlalchemy import Engine
else:
    Engine = object

_MIGRATION_DIR = Path(__file__).parent


def _make_config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_MIGRATION_DIR))
    return cfg


def get_current_revision(engine: Engine) -> str | None:
    """Return the current Alembic revision for the given engine, or None if untracked."""
    with engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def upgrade(engine: Engine, target: str = "head") -> None:
    """Upgrade the database to the given revision (default: head)."""
    cfg = _make_config()
    script = ScriptDirectory.from_config(cfg)

    def fn(rev: tuple[str, ...], _context: MigrationContext) -> list[Any]:
        return script._upgrade_revs(target, rev)  # type: ignore[arg-type]  # noqa: SLF001

    with EnvironmentContext(cfg, script, fn=fn, destination_rev=target) as env:
        with engine.connect() as conn:
            env.configure(
                connection=conn,
                target_metadata=SQLModel.metadata,
                render_as_batch=True,
            )
            with env.begin_transaction():
                env.run_migrations()


def downgrade(engine: Engine, target: str) -> None:
    """Downgrade the database to the given revision."""
    cfg = _make_config()
    script = ScriptDirectory.from_config(cfg)

    def fn(rev: tuple[str, ...], _context: MigrationContext) -> list[Any]:
        return script._downgrade_revs(target, rev)  # type: ignore[arg-type]  # noqa: SLF001

    with EnvironmentContext(cfg, script, fn=fn, destination_rev=target) as env:
        with engine.connect() as conn:
            env.configure(
                connection=conn,
                target_metadata=SQLModel.metadata,
                render_as_batch=True,
            )
            with env.begin_transaction():
                env.run_migrations()

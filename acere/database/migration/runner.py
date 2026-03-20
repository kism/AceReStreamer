"""Programmatic Alembic migration runner."""

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

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


def _backup_database_if_needed(engine: Engine, target: str) -> None:
    """Back up the SQLite database file before a schema migration."""
    current = get_current_revision(engine)

    # Resolve "head" to the actual target revision
    cfg = _make_config(engine)
    script_dir = ScriptDirectory.from_config(cfg)
    resolved_target = target
    if target == "head":
        head = script_dir.get_current_head()
        if head is not None:
            resolved_target = head

    if current == resolved_target:
        return

    db_url = str(engine.url)
    if not db_url.startswith("sqlite:///"):
        return

    db_path = Path(db_url.removeprefix("sqlite:///"))
    if not db_path.exists():
        return

    backup_dir = db_path.parent / "db_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    revision_label = current or "none"
    backup_name = f"{db_path.stem}_{timestamp}_rev{revision_label}{db_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(db_path, backup_path)


def upgrade(engine: Engine, target: str = "head") -> None:
    """Upgrade the database to the given revision (default: head)."""
    _backup_database_if_needed(engine, target)
    command.upgrade(_make_config(engine), target)


def downgrade(engine: Engine, target: str) -> None:
    """Downgrade the database to the given revision."""
    _backup_database_if_needed(engine, target)
    command.downgrade(_make_config(engine), target)

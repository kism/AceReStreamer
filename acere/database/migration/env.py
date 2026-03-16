"""Alembic environment for acere database migrations."""

from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

# Import all models so SQLModel.metadata is fully populated
import acere.database.models
import acere.database.models.user  # noqa: F401
from acere.database.init import engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _get_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    return str(engine.url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL, no live DB connection)."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


run_migrations_offline()

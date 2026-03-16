"""Alembic environment for acere database migrations."""

from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

# Import all models so SQLModel.metadata is fully populated
import acere.database.models
import acere.database.models.user  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL, no live DB connection)."""
    from acere.database.init import engine  # noqa: PLC0415

    url = config.get_main_option("sqlalchemy.url") or str(engine.url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a live database connection."""
    connectable = config.attributes.get("engine")
    if connectable is None:
        from acere.database.init import engine  # noqa: PLC0415

        connectable = engine

    with connectable.connect() as conn:
        context.configure(
            connection=conn,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

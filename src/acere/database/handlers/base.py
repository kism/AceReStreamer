from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlmodel import Session, SQLModel

from acere.database.init import engine

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine.base import Engine
else:
    Generator = object
    Engine = object


class BaseDatabaseHandler:
    """Base class for database handlers."""

    def __init__(self, test_engine: Engine | None = None) -> None:
        """Initialize the database handler."""
        self._engine = test_engine or engine
        SQLModel.metadata.create_all(self._engine)

    @contextmanager
    def _get_session(self) -> Generator[Session]:
        """Get a database session as a context manager."""
        with Session(self._engine) as session:
            yield session

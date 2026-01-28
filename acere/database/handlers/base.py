from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlmodel import Session, SQLModel

from acere.database.init import engine

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine.base import Engine
else:
    Iterator = object
    Engine = object


class BaseDatabaseHandler:
    """Base class for database handlers."""

    def __init__(self, test_engine: Engine | None = None) -> None:
        """Initialize the database handler."""
        self._engine = test_engine if test_engine else engine
        SQLModel.metadata.create_all(self._engine)

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Get a database session as a context manager."""
        with Session(self._engine) as session:
            yield session

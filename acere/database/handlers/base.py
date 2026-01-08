from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel

from acere.core.db import engine


class BaseDatabaseHandler:
    """Base class for database handlers."""

    def __init__(self) -> None:
        SQLModel.metadata.create_all(engine)

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Get a database session as a context manager."""
        with Session(engine) as session:
            yield session

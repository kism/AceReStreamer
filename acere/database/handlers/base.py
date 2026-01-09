from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlmodel import Session, SQLModel

from acere.core.db import engine

if TYPE_CHECKING:
    from collections.abc import Iterator
else:
    Iterator = object


class BaseDatabaseHandler:
    """Base class for database handlers."""

    def __init__(self) -> None:
        SQLModel.metadata.create_all(engine)

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Get a database session as a context manager."""
        with Session(engine) as session:
            yield session

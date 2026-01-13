"""Main database instance module."""

from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from acere.constants import DATABASE_FILE

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


class DatabaseInstance:
    """Database instance."""

    def __init__(self, database_path: Path = DATABASE_FILE) -> None:
        """Initialize the database instance."""
        self._engine = create_engine(f"sqlite:///{database_path}")

        self.session = sessionmaker(bind=self._engine)()

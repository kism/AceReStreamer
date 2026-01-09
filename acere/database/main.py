"""Main database instance module."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_PATH = Path("./instance/acerestreamer.db")


class DatabaseInstance:
    """Database instance."""

    def __init__(self, database_path: Path = DEFAULT_DB_PATH) -> None:
        """Initialize the database instance."""
        self._engine = create_engine(f"sqlite:///{database_path}")

        self.session = sessionmaker(bind=self._engine)()

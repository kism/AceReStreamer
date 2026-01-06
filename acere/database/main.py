"""Main database instance module."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseInstance:
    """Database instance."""

    def __init__(self) -> None:
        """Initialize the database instance."""

        databse_path = Path("./instance/acerestreamer.db")

        self._engine = create_engine(f"sqlite:///{databse_path}")

        self.session = sessionmaker(bind=self._engine)()

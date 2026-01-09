from pathlib import Path

from acere.database.main import DatabaseInstance


def test_init_database_instance(tmp_path: Path) -> None:
    """Test initializing the DatabaseInstance."""
    DatabaseInstance(database_path=tmp_path / "test.db")

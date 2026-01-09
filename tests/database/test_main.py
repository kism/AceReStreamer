from typing import TYPE_CHECKING

from acere.database.main import DatabaseInstance

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


def test_init_database_instance(tmp_path: Path) -> None:
    """Test initializing the DatabaseInstance."""
    DatabaseInstance(database_path=tmp_path / "test.db")

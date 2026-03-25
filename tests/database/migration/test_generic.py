"""Generic migration tests that are not tied to a specific schema version."""

from typing import TYPE_CHECKING

import pytest
from sqlmodel import SQLModel, create_engine

from acere.database.migration import runner

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

    from sqlalchemy import Engine
else:
    Callable = object
    Generator = object
    Path = object
    Engine = object


@pytest.fixture
def engine(tmp_path: Path) -> Generator[Engine, None, None]:
    e = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)
    yield e
    e.dispose()


def test_fresh_install(
    engine: Engine,
    get_columns: Callable[[Engine, str], set[str]],
    get_tables: Callable[[Engine], set[str]],
) -> None:
    """create_all + upgrade to head on an empty DB produces the expected schema."""
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)

    tables = get_tables(engine)
    assert "quality_cache" in tables
    assert "alembic_version" in tables
    assert "xc_stream_map" in tables

    columns = get_columns(engine, "quality_cache")
    assert "last_quality_success_time" in columns
    assert "has_ever_worked" not in columns
    assert "hls_identifier" in columns
    assert "content_id" not in columns


def test_get_current_revision(engine: Engine) -> None:
    """get_current_revision returns None before any migrations, then tracks applied revision."""
    assert runner.get_current_revision(engine) is None

    # create_all mirrors real usage: tables exist before migrations run
    SQLModel.metadata.create_all(engine)

    runner.upgrade(engine, "0001")
    assert runner.get_current_revision(engine) == "0001"

    runner.upgrade(engine)
    assert runner.get_current_revision(engine) == "0003"

    runner.downgrade(engine, "0001")
    assert runner.get_current_revision(engine) == "0001"

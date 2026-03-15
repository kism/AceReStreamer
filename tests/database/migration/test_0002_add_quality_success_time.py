"""Tests for migration 0002: add last_quality_success_time, drop has_ever_worked."""

from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa
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

_OLD_QUALITY_CACHE_DDL = (
    "CREATE TABLE ace_quality_cache ("
    "  content_id TEXT PRIMARY KEY NOT NULL,"
    "  quality INTEGER NOT NULL,"
    "  m3u_failures INTEGER NOT NULL,"
    "  has_ever_worked BOOLEAN NOT NULL DEFAULT 0"
    ")"
)


@pytest.fixture
def engine(tmp_path: Path) -> Generator[Engine, None, None]:
    e = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)
    yield e
    e.dispose()


def test_0002_upgrade_from_old_schema(engine: Engine, get_columns: Callable[[Engine, str], set[str]]) -> None:
    """Migration 0002 adds last_quality_success_time and drops has_ever_worked from old schema."""
    with engine.connect() as conn:
        conn.execute(sa.text(_OLD_QUALITY_CACHE_DDL))
        conn.commit()

    columns_before = get_columns(engine, "ace_quality_cache")
    assert "has_ever_worked" in columns_before
    assert "last_quality_success_time" not in columns_before

    runner.upgrade(engine)

    columns_after = get_columns(engine, "ace_quality_cache")
    assert "last_quality_success_time" in columns_after
    assert "has_ever_worked" not in columns_after


def test_0002_upgrade_idempotent(engine: Engine, get_columns: Callable[[Engine, str], set[str]]) -> None:
    """Running upgrade to head twice does not raise and leaves the schema correct."""
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)
    runner.upgrade(engine)

    columns = get_columns(engine, "ace_quality_cache")
    assert "last_quality_success_time" in columns
    assert "has_ever_worked" not in columns


def test_0002_downgrade_restores_old_schema(engine: Engine, get_columns: Callable[[Engine, str], set[str]]) -> None:
    """Downgrading 0002 → 0001 restores has_ever_worked and removes last_quality_success_time."""
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)

    runner.downgrade(engine, "0001")

    columns = get_columns(engine, "ace_quality_cache")
    assert "has_ever_worked" in columns
    assert "last_quality_success_time" not in columns

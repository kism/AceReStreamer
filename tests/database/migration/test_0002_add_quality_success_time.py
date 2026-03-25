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

_OLD_USER_DDL = (
    "CREATE TABLE user ("
    "  id TEXT PRIMARY KEY NOT NULL,"
    "  username TEXT NOT NULL UNIQUE,"
    "  is_active BOOLEAN NOT NULL DEFAULT 1,"
    "  is_superuser BOOLEAN NOT NULL DEFAULT 0,"
    "  stream_token TEXT NOT NULL,"
    "  full_name TEXT,"
    "  hashed_password TEXT NOT NULL"
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
        conn.execute(sa.text(_OLD_USER_DDL))
        conn.commit()

    columns_before = get_columns(engine, "ace_quality_cache")
    assert "has_ever_worked" in columns_before
    assert "last_quality_success_time" not in columns_before

    # After upgrade to head (0003), table is renamed to quality_cache with hls_identifier
    runner.upgrade(engine)

    columns_after = get_columns(engine, "quality_cache")
    assert "last_quality_success_time" in columns_after
    assert "has_ever_worked" not in columns_after
    assert "hls_identifier" in columns_after

    user_columns_after = get_columns(engine, "user")
    assert "password_changed_at" in user_columns_after


def test_0002_upgrade_idempotent(engine: Engine, get_columns: Callable[[Engine, str], set[str]]) -> None:
    """Running upgrade to head twice does not raise and leaves the schema correct."""
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)
    runner.upgrade(engine)

    # After upgrade to head, table is quality_cache with hls_identifier
    columns = get_columns(engine, "quality_cache")
    assert "last_quality_success_time" in columns
    assert "has_ever_worked" not in columns
    assert "hls_identifier" in columns


def test_0002_downgrade_restores_old_schema(engine: Engine, get_columns: Callable[[Engine, str], set[str]]) -> None:
    """Downgrading 0002 -> 0001 restores has_ever_worked and removes last_quality_success_time."""
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)

    # After downgrade to 0001, 0003 downgrade reverses the rename, then 0002 downgrade restores has_ever_worked
    runner.downgrade(engine, "0001")

    columns = get_columns(engine, "ace_quality_cache")
    assert "has_ever_worked" in columns
    assert "last_quality_success_time" not in columns
    assert "content_id" in columns

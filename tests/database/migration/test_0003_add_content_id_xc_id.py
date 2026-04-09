"""Tests for migration 0003: add content_id_xc_id mapping table."""

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


@pytest.fixture
def engine(tmp_path: Path) -> Generator[Engine, None, None]:
    e = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)
    yield e
    e.dispose()


def test_0003_upgrade_creates_table(engine: Engine, get_tables: Callable[[Engine], set[str]]) -> None:
    """Migration 0003 creates content_id_xc_id table."""
    SQLModel.metadata.create_all(engine)
    # Drop the table so migration can create it
    with engine.connect() as conn:
        conn.execute(sa.text("DROP TABLE IF EXISTS content_id_xc_id"))
        conn.commit()

    runner.upgrade(engine)

    assert "content_id_xc_id" in get_tables(engine)


def test_0003_seeds_from_ace_streams(engine: Engine) -> None:
    """Migration 0003 seeds mappings from existing ace_streams rows."""
    # Create prerequisite tables so earlier migrations don't fail
    with engine.connect() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS ace_quality_cache ("
                "  content_id TEXT PRIMARY KEY NOT NULL,"
                "  quality INTEGER NOT NULL,"
                "  m3u_failures INTEGER NOT NULL,"
                "  has_ever_worked BOOLEAN NOT NULL DEFAULT 0"
                ")"
            )
        )
        conn.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS user ("
                "  id TEXT PRIMARY KEY NOT NULL,"
                "  username TEXT NOT NULL UNIQUE,"
                "  is_active BOOLEAN NOT NULL DEFAULT 1,"
                "  is_superuser BOOLEAN NOT NULL DEFAULT 0,"
                "  stream_token TEXT NOT NULL,"
                "  full_name TEXT,"
                "  hashed_password TEXT NOT NULL"
                ")"
            )
        )
        conn.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS ace_streams ("
                "  id INTEGER PRIMARY KEY,"
                "  content_id TEXT NOT NULL UNIQUE,"
                "  title TEXT DEFAULT '',"
                "  infohash TEXT,"
                "  tvg_id TEXT,"
                "  tvg_logo TEXT,"
                "  group_title TEXT DEFAULT '',"
                "  last_scraped_time DATETIME"
                ")"
            )
        )
        conn.execute(sa.text("INSERT INTO ace_streams (id, content_id, title) VALUES (42, 'abc123def456', 'Test')"))
        conn.execute(sa.text("INSERT INTO ace_streams (id, content_id, title) VALUES (99, 'xyz789ghi012', 'Test2')"))
        conn.commit()

    runner.upgrade(engine)

    with engine.connect() as conn:
        rows = conn.execute(sa.text("SELECT xc_id, content_id FROM content_id_xc_id ORDER BY xc_id")).fetchall()

    assert len(rows) == 2
    assert rows[0] == (42, "abc123def456")
    assert rows[1] == (99, "xyz789ghi012")


def test_0003_upgrade_idempotent(engine: Engine, get_tables: Callable[[Engine], set[str]]) -> None:
    """Running upgrade to head twice does not raise."""
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)
    runner.upgrade(engine)

    assert "content_id_xc_id" in get_tables(engine)


def test_0003_downgrade_removes_table(engine: Engine, get_tables: Callable[[Engine], set[str]]) -> None:
    """Downgrading 0003 → 0002 removes content_id_xc_id table."""
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)

    runner.downgrade(engine, "0002")

    assert "content_id_xc_id" not in get_tables(engine)

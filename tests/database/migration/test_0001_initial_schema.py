"""Tests for migration 0001: initial schema cleanup."""

from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa
from sqlmodel import create_engine

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

_LEGACY_TABLES = ["acequalitycache", "contentidinfohash", "content_id_infohash", "content_id_xc_id"]


@pytest.fixture
def engine(tmp_path: Path) -> Generator[Engine, None, None]:
    e = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)
    yield e
    e.dispose()


def test_0001_drops_legacy_tables(engine: Engine, get_tables: Callable[[Engine], set[str]]) -> None:
    """Migration 0001 drops all known legacy tables."""
    with engine.connect() as conn:
        for table in _LEGACY_TABLES:
            conn.execute(sa.text(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)"))
        conn.commit()

    assert set(_LEGACY_TABLES).issubset(get_tables(engine))

    runner.upgrade(engine, "0001")

    remaining = get_tables(engine)
    for table in _LEGACY_TABLES:
        assert table not in remaining


def test_0001_idempotent_without_legacy_tables(engine: Engine) -> None:
    """Migration 0001 succeeds when no legacy tables are present (IF EXISTS guard)."""
    runner.upgrade(engine, "0001")

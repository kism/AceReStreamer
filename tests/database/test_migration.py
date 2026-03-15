"""Tests for database migrations."""

from pathlib import Path
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlmodel import SQLModel, create_engine

from acere.database.migration import runner

if TYPE_CHECKING:
    from sqlalchemy import Engine
else:
    Engine = object

_LEGACY_TABLES = ["acequalitycache", "contentidinfohash", "content_id_infohash", "content_id_xc_id"]

_OLD_QUALITY_CACHE_DDL = (
    "CREATE TABLE ace_quality_cache ("
    "  content_id TEXT PRIMARY KEY NOT NULL,"
    "  quality INTEGER NOT NULL,"
    "  m3u_failures INTEGER NOT NULL,"
    "  has_ever_worked BOOLEAN NOT NULL DEFAULT 0"
    ")"
)


def _get_columns(engine: Engine, table_name: str) -> set[str]:
    with engine.connect() as conn:
        result = conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
        return {row[1] for row in result.fetchall()}


def _get_tables(engine: Engine) -> set[str]:
    with engine.connect() as conn:
        result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
        return {row[0] for row in result.fetchall()}


def test_fresh_install(tmp_path: Path) -> None:
    """create_all + upgrade to head on an empty DB produces the expected schema."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)

    tables = _get_tables(engine)
    assert "ace_quality_cache" in tables
    assert "alembic_version" in tables

    columns = _get_columns(engine, "ace_quality_cache")
    assert "last_quality_success_time" in columns
    assert "has_ever_worked" not in columns

    engine.dispose()


def test_0001_drops_legacy_tables(tmp_path: Path) -> None:
    """Migration 0001 drops all known legacy tables."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    with engine.connect() as conn:
        for table in _LEGACY_TABLES:
            conn.execute(sa.text(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)"))
        conn.commit()

    assert set(_LEGACY_TABLES).issubset(_get_tables(engine))

    runner.upgrade(engine, "0001")

    remaining = _get_tables(engine)
    for table in _LEGACY_TABLES:
        assert table not in remaining

    engine.dispose()


def test_0001_idempotent_without_legacy_tables(tmp_path: Path) -> None:
    """Migration 0001 succeeds when no legacy tables are present (IF EXISTS guard)."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    runner.upgrade(engine, "0001")

    engine.dispose()


def test_0002_upgrade_from_old_schema(tmp_path: Path) -> None:
    """Migration 0002 adds last_quality_success_time and drops has_ever_worked from old schema."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    with engine.connect() as conn:
        conn.execute(sa.text(_OLD_QUALITY_CACHE_DDL))
        conn.commit()

    columns_before = _get_columns(engine, "ace_quality_cache")
    assert "has_ever_worked" in columns_before
    assert "last_quality_success_time" not in columns_before

    runner.upgrade(engine)

    columns_after = _get_columns(engine, "ace_quality_cache")
    assert "last_quality_success_time" in columns_after
    assert "has_ever_worked" not in columns_after

    engine.dispose()


def test_0002_upgrade_idempotent(tmp_path: Path) -> None:
    """Running upgrade to head twice does not raise and leaves the schema correct."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)
    runner.upgrade(engine)

    columns = _get_columns(engine, "ace_quality_cache")
    assert "last_quality_success_time" in columns
    assert "has_ever_worked" not in columns

    engine.dispose()


def test_0002_downgrade_restores_old_schema(tmp_path: Path) -> None:
    """Downgrading 0002 → 0001 restores has_ever_worked and removes last_quality_success_time."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)

    runner.downgrade(engine, "0001")

    columns = _get_columns(engine, "ace_quality_cache")
    assert "has_ever_worked" in columns
    assert "last_quality_success_time" not in columns

    engine.dispose()


def test_get_current_revision(tmp_path: Path) -> None:
    """get_current_revision returns None before any migrations, then tracks applied revision."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    assert runner.get_current_revision(engine) is None

    # create_all mirrors real usage: tables exist before migrations run
    SQLModel.metadata.create_all(engine)

    runner.upgrade(engine, "0001")
    assert runner.get_current_revision(engine) == "0001"

    runner.upgrade(engine)
    assert runner.get_current_revision(engine) == "0002"

    runner.downgrade(engine, "0001")
    assert runner.get_current_revision(engine) == "0001"

    engine.dispose()

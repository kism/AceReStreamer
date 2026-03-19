"""Shared helpers for migration tests."""

from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy import Engine
else:
    Callable = object
    Engine = object


@pytest.fixture
def get_columns() -> Callable[[Engine, str], set[str]]:
    """Return a helper that fetches column names for a table."""

    def _get_columns(engine: Engine, table_name: str) -> set[str]:
        with engine.connect() as conn:
            result = conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
            return {row[1] for row in result.fetchall()}

    return _get_columns


@pytest.fixture
def get_tables() -> Callable[[Engine], set[str]]:
    """Return a helper that fetches all table names in the database."""

    def _get_tables(engine: Engine) -> set[str]:
        with engine.connect() as conn:
            result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            return {row[0] for row in result.fetchall()}

    return _get_tables

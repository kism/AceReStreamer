"""Custom SQLAlchemy types for the database."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, TypeDecorator


class TZDateTime(TypeDecorator[datetime]):
    """A DateTime type that ensures timezone-aware datetimes.

    SQLite strips timezone info from stored datetimes. This TypeDecorator
    assumes UTC for all stored values and restores tzinfo on read.
    Runs at the SQLAlchemy level, so it works for ORM loads too.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

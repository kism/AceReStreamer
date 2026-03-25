"""IPTV proxy pool API response models."""

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, computed_field

from acere.services.pool.entry import BasePoolEntry


class IPTVPoolEntryForAPI(BaseModel):
    """API representation of a single IPTV pool entry."""

    slug: str
    source_name: str
    date_started: datetime
    last_used: datetime
    locked_in: bool
    time_until_unlock_seconds: int
    time_running_seconds: int

    @staticmethod
    def from_entry(entry: BasePoolEntry, source_name: str) -> IPTVPoolEntryForAPI:
        """Create an API model from a pool entry."""
        locked_in = entry.check_locked_in()
        time_until_unlock = entry.get_time_until_unlock() if locked_in else timedelta(seconds=0)
        time_running = datetime.now(tz=UTC) - entry.date_started

        return IPTVPoolEntryForAPI(
            slug=entry.key,
            source_name=source_name,
            date_started=entry.date_started,
            last_used=entry.date_last_used,
            locked_in=locked_in,
            time_until_unlock_seconds=max(0, int(time_until_unlock.total_seconds())),
            time_running_seconds=int(time_running.total_seconds()),
        )


class IPTVPoolSourceForAPI(BaseModel):
    """API representation of a single source's pool."""

    source_name: str
    max_size: int
    entries: list[IPTVPoolEntryForAPI]

    @computed_field
    @property
    def active_count(self) -> int:
        """Number of active entries."""
        return len(self.entries)


class IPTVPoolForAPI(BaseModel):
    """API representation of all IPTV source pools."""

    sources: list[IPTVPoolSourceForAPI]

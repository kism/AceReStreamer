"""IPTV proxy pool entry."""

from acere.services.pool.entry import BasePoolEntry


class IPTVPoolEntry(BasePoolEntry):
    """Pool entry for an active IPTV proxy stream."""

    def __init__(self, slug: str, source_name: str) -> None:
        """Initialize an IPTV pool entry."""
        super().__init__(key=slug)
        self.source_name = source_name

    @property
    def slug(self) -> str:
        """Stream slug (alias for key)."""
        return self.key

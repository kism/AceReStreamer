"""IPTV Streams database handler instance."""

from acere.database.handlers.iptv_streams import IPTVStreamDBHandler

_iptv_streams_handler: IPTVStreamDBHandler | None = None


def get_iptv_streams_db_handler() -> IPTVStreamDBHandler:
    """Get the IPTV streams database handler, creating it if needed."""
    global _iptv_streams_handler
    if _iptv_streams_handler is None:
        _iptv_streams_handler = IPTVStreamDBHandler()
    return _iptv_streams_handler

"""XC stream map database handler instance."""

from acere.database.handlers.xc_stream_map import XCStreamMapHandler

_xc_stream_map_handler: XCStreamMapHandler | None = None


def get_xc_stream_map_handler() -> XCStreamMapHandler:
    """Get the XC stream map database handler, creating it if needed."""
    global _xc_stream_map_handler
    if _xc_stream_map_handler is None:
        _xc_stream_map_handler = XCStreamMapHandler()
    return _xc_stream_map_handler

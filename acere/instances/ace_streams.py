from acere.database.handlers.acestreams import AceStreamDBHandler

_ace_streams_handler: AceStreamDBHandler | None = None


def get_ace_streams_db_handler() -> AceStreamDBHandler:
    """Get the global AceStreamsDBHandler instance."""
    global _ace_streams_handler  # noqa: PLW0603
    if _ace_streams_handler is None:
        _ace_streams_handler = AceStreamDBHandler()
    return _ace_streams_handler

from acere.database.handlers.content_id_xc_id import ContentIdXcIdDatabaseHandler

_xc_stream_handler: ContentIdXcIdDatabaseHandler | None = None


def get_xc_stream_db_handler() -> ContentIdXcIdDatabaseHandler:
    """Get the global ContentIdXcIdDatabaseHandler instance."""
    global _xc_stream_handler
    if _xc_stream_handler is None:
        _xc_stream_handler = ContentIdXcIdDatabaseHandler()
    return _xc_stream_handler

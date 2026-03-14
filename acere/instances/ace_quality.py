"""Global instance for the quality cache handler."""

from acere.database.handlers.quality_cache import AceQualityCacheHandler

_quality_handler: AceQualityCacheHandler | None = None


def get_quality_handler() -> AceQualityCacheHandler:
    """Get the global AceQualityCacheHandler instance."""
    if _quality_handler is None:
        msg = "AceQualityCacheHandler instance is not set."
        raise ValueError(msg)
    return _quality_handler


def set_quality_handler(handler: AceQualityCacheHandler) -> None:
    """Set the global AceQualityCacheHandler instance."""
    global _quality_handler  # noqa: PLW0603
    _quality_handler = handler
    handler.start_daily_check_thread()

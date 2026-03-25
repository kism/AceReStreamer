"""Global instance for the quality cache handler."""

from acere.database.handlers.quality_cache import QualityCacheHandler

_quality_handler: QualityCacheHandler | None = None


def get_quality_handler() -> QualityCacheHandler:
    """Get the global QualityCacheHandler instance."""
    if _quality_handler is None:
        msg = "QualityCacheHandler instance is not set."
        raise ValueError(msg)
    return _quality_handler


def set_quality_handler(handler: QualityCacheHandler) -> None:
    """Set the global QualityCacheHandler instance."""
    global _quality_handler
    _quality_handler = handler

from acere.database.handlers.quality_cache import AceQualityCacheHandler

_cache_handler: AceQualityCacheHandler | None = AceQualityCacheHandler()


def get_quality_handler() -> AceQualityCacheHandler:
    """Get the global cache handler."""
    global _cache_handler  # noqa: PLW0603
    if _cache_handler is None:
        _cache_handler = AceQualityCacheHandler()
    return _cache_handler

from acere.services.ace_pool.pool import AcePool

_ace_pool: AcePool | None = None


def set_ace_pool(pool: AcePool) -> None:
    """Set the global AcePool instance."""
    global _ace_pool  # noqa: PLW0603 Lazy Loading
    _ace_pool = pool


def get_ace_pool() -> AcePool:
    """Get the global AcePool instance."""
    if _ace_pool is None:
        msg = "AcePool instance is not set."
        raise ValueError(msg)
    return _ace_pool

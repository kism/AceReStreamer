from acere.services.ace_pool.pool import AcePool

_ace_pool: AcePool | None = None


def set_ace_pool(pool: AcePool) -> None:
    """Set the global AcePool instance."""
    global _ace_pool
    _ace_pool = pool


def get_ace_pool() -> AcePool:
    """Get the global AcePool instance."""
    if _ace_pool is None:
        raise ValueError("AcePool instance is not set.")
    return _ace_pool

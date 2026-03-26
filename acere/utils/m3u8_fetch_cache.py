"""Async cache for URL fetches with request coalescing."""

import asyncio
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class FetchCache[T]:
    """Generic async fetch cache with TTL and request coalescing.

    - TTL-based expiry (default 3 seconds).
    - Request coalescing: concurrent fetches for the same URL await a single
      in-flight request rather than hammering the upstream.
    """

    def __init__(self, ttl: float = 3.0) -> None:
        self._ttl = ttl
        self._cache: dict[str, tuple[T, float]] = {}
        self._inflight: dict[str, asyncio.Future[T]] = {}

    async def get(self, url: str, fetch: Callable[[str], Awaitable[T]]) -> T:
        """Return cached value for *url*, fetching via *fetch* if needed.

        If another coroutine is already fetching *url*, this call awaits that
        result instead of issuing a duplicate request.
        """
        now = time.monotonic()

        # Fast path: unexpired cache hit
        if url in self._cache:
            value, expires_at = self._cache[url]
            if expires_at > now:
                return value

        # Join an in-flight fetch for the same URL (no await between checks —
        # asyncio single-threaded guarantee makes this safe)
        if url in self._inflight:
            return await self._inflight[url]

        # Start a new fetch and publish the future so waiters can join
        future: asyncio.Future[T] = asyncio.get_running_loop().create_future()
        self._inflight[url] = future

        try:
            value = await fetch(url)
            self._cache[url] = (value, time.monotonic() + self._ttl)
            future.set_result(value)
        except Exception as exc:
            future.set_exception(exc)
            raise
        else:
            return value
        finally:
            self._inflight.pop(url, None)

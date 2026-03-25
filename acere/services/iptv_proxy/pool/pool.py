"""IPTV proxy pool manager — per-source stream tracking with lock-in."""

import threading

from acere.instances.config import settings
from acere.services.pool.pool import BasePool
from acere.utils.logger import get_logger

from .entry import IPTVPoolEntry
from .models import IPTVPoolEntryForAPI, IPTVPoolForAPI, IPTVPoolSourceForAPI

logger = get_logger(__name__)


class IPTVPoolManager:
    """Manages per-source pools for IPTV proxy streams.

    Each IPTV source gets its own pool with the source's max_active_streams limit.
    A max_active_streams of 0 means unlimited (no pool enforcement).
    """

    def __init__(self, instance_id: str = "") -> None:
        """Initialize the IPTV pool manager."""
        self._instance_id = instance_id
        self._source_pools: dict[str, BasePool[IPTVPoolEntry]] = {}
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()

    def check_in(self, slug: str, source_name: str) -> bool:
        """Register or update a stream in its source pool.

        Returns True if the stream is allowed, False if the pool is full and all entries are locked in.
        """
        max_active = self._get_max_active_streams(source_name)
        if max_active == 0:
            return True  # Unlimited

        pool = self._get_or_create_pool(source_name, max_active)

        # Already tracked?
        existing = pool.get_entry(slug)
        if existing:
            existing.update_last_used()
            return True

        # Has capacity?
        if pool.has_capacity:
            pool.add_entry(slug, IPTVPoolEntry(slug=slug, source_name=source_name))
            logger.info("IPTV pool [%s]: added stream %s (%d/%d)", source_name, slug, pool.active_count, max_active)
            return True

        # Try eviction
        evicted_key = pool.try_evict_one()
        if evicted_key is not None:
            pool.add_entry(slug, IPTVPoolEntry(slug=slug, source_name=source_name))
            logger.info(
                "IPTV pool [%s]: evicted %s, added %s (%d/%d)",
                source_name,
                evicted_key,
                slug,
                pool.active_count,
                max_active,
            )
            return True

        logger.warning("IPTV pool [%s]: full (%d/%d), all locked in", source_name, pool.active_count, max_active)
        return False

    def touch(self, slug: str) -> None:
        """Update last-used timestamp for a stream if it is tracked in any pool."""
        for pool in self._source_pools.values():
            entry = pool.get_entry(slug)
            if entry:
                entry.update_last_used()
                return

    def remove_entry(self, source_name: str, slug: str) -> bool:
        """Remove a specific entry from a source pool."""
        pool = self._source_pools.get(source_name)
        if pool:
            return pool.remove_entry(slug)
        return False

    def _get_or_create_pool(self, source_name: str, max_size: int) -> BasePool[IPTVPoolEntry]:
        """Get or create a pool for a source."""
        if source_name not in self._source_pools:
            self._source_pools[source_name] = BasePool(
                instance_id=f"{self._instance_id}:iptv:{source_name}",
                max_size=max_size,
            )
        pool = self._source_pools[source_name]
        # Update max_size in case config changed
        pool._max_size = max_size  # noqa: SLF001
        return pool

    def _get_max_active_streams(self, source_name: str) -> int:
        """Look up max_active_streams from config for a source."""
        iptv_conf = settings.iptv
        for xtream_source in iptv_conf.xtream:
            if xtream_source.name == source_name:
                return xtream_source.max_active_streams
        for m3u8_source in iptv_conf.m3u8:
            if m3u8_source.name == source_name:
                return m3u8_source.max_active_streams
        return 0  # Unknown source = unlimited

    def start_cleanup_thread(self) -> None:
        """Start a background thread that cleans stale entries from all source pools."""

        def cleanup_loop() -> None:
            while not self._stop_event.is_set():
                if self._stop_event.wait(10):
                    break
                for source_name, pool in list(self._source_pools.items()):
                    removed = pool.cleanup_stale()
                    if removed:
                        logger.debug(
                            "IPTV pool [%s]: cleaned %d stale entries",
                            source_name,
                            len(removed),
                        )

        self.stop_all_threads()
        thread = threading.Thread(
            target=cleanup_loop,
            name=f"IPTVPoolManager: cleanup [{self._instance_id}]",
            daemon=True,
        )
        thread.start()
        self._threads.append(thread)

    def stop_all_threads(self) -> None:
        """Stop the cleanup thread."""
        if len(self._threads) == 0:
            return

        logger.info("Stopping IPTVPoolManager threads [%s]", self._instance_id)
        self._stop_event.set()
        for thread in self._threads.copy():
            if thread.is_alive():
                thread.join(timeout=60)
                if not thread.is_alive():
                    self._threads.remove(thread)
                else:
                    logger.warning("Thread %s did not stop in time.", thread.name)

        self._stop_event.clear()

    # region API
    def get_pool_status_by_source(self, source_name: str) -> IPTVPoolSourceForAPI | None:
        """Get pool status for a single source."""
        pool = self._source_pools.get(source_name)
        if not pool:
            return None

        entries = [IPTVPoolEntryForAPI.from_entry(entry, source_name) for entry in pool.get_all_entries().values()]
        return IPTVPoolSourceForAPI(
            source_name=source_name,
            max_size=pool.max_size,
            entries=entries,
        )

    def get_all_pool_status(self) -> IPTVPoolForAPI:
        """Get pool status for all sources."""
        sources: list[IPTVPoolSourceForAPI] = []
        for source_name in self._source_pools:
            status = self.get_pool_status_by_source(source_name)
            if status:
                sources.append(status)
        return IPTVPoolForAPI(sources=sources)

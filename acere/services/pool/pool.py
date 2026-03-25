"""Generic pool with entry tracking, LRU eviction, and background cleanup."""

import threading

from acere.utils.logger import get_logger

from .entry import BasePoolEntry

logger = get_logger(__name__)


class BasePool[T: BasePoolEntry]:
    """Base pool with entry tracking, LRU eviction of non-locked entries, and stale cleanup.

    Subclasses may override _on_entry_removed() to perform cleanup when entries are evicted.
    A max_size of 0 means unlimited capacity.
    """

    def __init__(self, instance_id: str, max_size: int) -> None:
        """Initialize the pool."""
        self._instance_id = instance_id
        self._max_size = max_size
        self._entries: dict[str, T] = {}
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()

    @property
    def max_size(self) -> int:
        """Maximum pool size (0 = unlimited)."""
        return self._max_size

    @property
    def active_count(self) -> int:
        """Number of active entries in the pool."""
        return len(self._entries)

    @property
    def is_full(self) -> bool:
        """Whether the pool has reached max capacity. Always False if max_size is 0 (unlimited)."""
        if self._max_size == 0:
            return False
        return len(self._entries) >= self._max_size

    @property
    def has_capacity(self) -> bool:
        """Whether the pool can accept new entries."""
        return not self.is_full

    def get_entry(self, key: str) -> T | None:
        """Get an entry by key, or None if not found."""
        return self._entries.get(key)

    def get_all_entries(self) -> dict[str, T]:
        """Get all entries in the pool."""
        return self._entries

    def add_entry(self, key: str, entry: T) -> None:
        """Add an entry to the pool."""
        self._entries[key] = entry

    def remove_entry(self, key: str) -> bool:
        """Remove an entry by key. Returns True if found and removed."""
        if key in self._entries:
            entry = self._entries.pop(key)
            self._on_entry_removed(key, entry)
            return True
        return False

    def try_evict_one(self) -> str | None:
        """Evict the least-recently-used non-locked entry. Returns evicted key or None."""
        shortlist = [entry for entry in self._entries.values() if not entry.check_locked_in()]

        if not shortlist:
            return None

        best = min(shortlist, key=lambda x: x.date_last_used)
        logger.info("Evicting entry '%s' from pool [%s]", best.key, self._instance_id)
        self.remove_entry(best.key)
        return best.key

    def cleanup_stale(self) -> list[str]:
        """Remove all stale entries. Returns list of removed keys."""
        stale_keys = [entry.key for entry in list(self._entries.values()) if entry.check_if_stale()]

        for key in stale_keys:
            logger.debug("Removing stale entry '%s' from pool [%s]", key, self._instance_id)
            self.remove_entry(key)

        return stale_keys

    def _on_entry_removed(self, key: str, entry: T) -> None:
        """Hook called when an entry is removed. Override for cleanup (e.g. stopping upstream connections)."""

    def _start_cleanup_thread(self, interval: int = 10) -> None:
        """Start a background thread that periodically removes stale entries."""

        def cleanup_loop() -> None:
            while not self._stop_event.is_set():
                if self._stop_event.wait(interval):
                    break
                self.cleanup_stale()

        self.stop_all_threads()
        thread = threading.Thread(
            target=cleanup_loop,
            name=f"BasePool: cleanup [{self._instance_id}]",
            daemon=True,
        )
        thread.start()
        self._threads.append(thread)

    def stop_all_threads(self) -> None:
        """Stop all background threads."""
        if len(self._threads) == 0:
            return

        logger.info("Stopping all %s threads [%s]", self.__class__.__name__, self._instance_id)
        self._stop_event.set()
        for thread in self._threads.copy():
            if thread.is_alive():
                thread.join(timeout=60)
                if not thread.is_alive():
                    self._threads.remove(thread)
                else:
                    logger.warning("Thread %s did not stop in time.", thread.name)

        self._stop_event.clear()

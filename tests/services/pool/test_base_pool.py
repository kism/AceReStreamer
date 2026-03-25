"""Tests for BasePool."""

from datetime import UTC, datetime, timedelta

from acere.services.pool.entry import BasePoolEntry
from acere.services.pool.pool import BasePool


def _make_entry(key: str, started_minutes_ago: int = 0, last_used_minutes_ago: int = 0) -> BasePoolEntry:
    """Helper to create a BasePoolEntry with specific timestamps."""
    entry = BasePoolEntry(key=key)
    now = datetime.now(tz=UTC)
    if started_minutes_ago:
        entry.date_started = now - timedelta(minutes=started_minutes_ago)
    if last_used_minutes_ago:
        entry.date_last_used = now - timedelta(minutes=last_used_minutes_ago)
    return entry


def test_pool_init() -> None:
    """Test pool initialization."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=3)
    assert pool.active_count == 0
    assert pool.is_full is False
    assert pool.has_capacity is True


def test_add_get_remove() -> None:
    """Test basic entry operations."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=3)
    entry = BasePoolEntry(key="a")

    pool.add_entry("a", entry)
    assert pool.active_count == 1
    assert pool.get_entry("a") is entry
    assert pool.get_entry("nonexistent") is None

    assert pool.remove_entry("a") is True
    assert pool.active_count == 0
    assert pool.remove_entry("a") is False  # Already removed


def test_capacity_enforcement() -> None:
    """Test that is_full and has_capacity work correctly."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=2)

    pool.add_entry("a", BasePoolEntry(key="a"))
    assert pool.is_full is False
    assert pool.has_capacity is True

    pool.add_entry("b", BasePoolEntry(key="b"))
    assert pool.is_full is True
    assert pool.has_capacity is False


def test_unlimited_pool() -> None:
    """Test that max_size=0 means unlimited."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=0)
    for i in range(100):
        pool.add_entry(str(i), BasePoolEntry(key=str(i)))
    assert pool.is_full is False
    assert pool.has_capacity is True
    assert pool.active_count == 100


def test_evict_one_lru() -> None:
    """Test that try_evict_one evicts the least recently used non-locked entry."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=3)

    # Add entries with different last_used times
    old_entry = _make_entry("old", started_minutes_ago=3, last_used_minutes_ago=10)
    mid_entry = _make_entry("mid", started_minutes_ago=3, last_used_minutes_ago=5)
    new_entry = _make_entry("new", started_minutes_ago=3, last_used_minutes_ago=1)

    pool.add_entry("old", old_entry)
    pool.add_entry("mid", mid_entry)
    pool.add_entry("new", new_entry)

    evicted = pool.try_evict_one()
    assert evicted == "old"
    assert pool.active_count == 2
    assert pool.get_entry("old") is None


def test_evict_one_respects_lock_in() -> None:
    """Test that try_evict_one skips locked-in entries."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=2)

    # Locked-in entry: old enough and recently used
    locked = _make_entry("locked", started_minutes_ago=10, last_used_minutes_ago=1)
    # Not locked: not old enough to lock in
    unlocked = _make_entry("unlocked", started_minutes_ago=3, last_used_minutes_ago=0)

    pool.add_entry("locked", locked)
    pool.add_entry("unlocked", unlocked)

    assert locked.check_locked_in() is True
    assert unlocked.check_locked_in() is False

    evicted = pool.try_evict_one()
    assert evicted == "unlocked"
    assert pool.get_entry("locked") is not None


def test_evict_one_all_locked_returns_none() -> None:
    """Test that try_evict_one returns None when all entries are locked in."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=2)

    locked1 = _make_entry("a", started_minutes_ago=10, last_used_minutes_ago=1)
    locked2 = _make_entry("b", started_minutes_ago=10, last_used_minutes_ago=1)

    pool.add_entry("a", locked1)
    pool.add_entry("b", locked2)

    assert locked1.check_locked_in() is True
    assert locked2.check_locked_in() is True

    evicted = pool.try_evict_one()
    assert evicted is None
    assert pool.active_count == 2


def test_cleanup_stale() -> None:
    """Test that cleanup_stale removes stale entries."""
    pool: BasePool[BasePoolEntry] = BasePool(instance_id="test", max_size=5)

    fresh = _make_entry("fresh")
    stale = _make_entry("stale", started_minutes_ago=3, last_used_minutes_ago=16)

    pool.add_entry("fresh", fresh)
    pool.add_entry("stale", stale)

    removed = pool.cleanup_stale()
    assert "stale" in removed
    assert "fresh" not in removed
    assert pool.active_count == 1
    assert pool.get_entry("fresh") is not None


def test_on_entry_removed_hook() -> None:
    """Test that _on_entry_removed is called when an entry is removed."""
    removed_keys: list[str] = []

    class TrackingPool(BasePool[BasePoolEntry]):
        def _on_entry_removed(self, key: str, entry: BasePoolEntry) -> None:
            removed_keys.append(key)

    pool = TrackingPool(instance_id="test", max_size=3)
    pool.add_entry("a", BasePoolEntry(key="a"))
    pool.remove_entry("a")
    assert removed_keys == ["a"]

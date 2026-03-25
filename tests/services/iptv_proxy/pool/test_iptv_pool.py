"""Tests for IPTVPoolManager."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from acere.services.iptv_proxy.pool.pool import IPTVPoolManager

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
else:
    MockerFixture = object


def _mock_settings_with_sources(mocker: MockerFixture, sources: dict[str, int]) -> None:
    """Mock settings.iptv with test sources and their max_active_streams values.

    sources: dict mapping source_name to max_active_streams.
    """

    class FakeSource:
        def __init__(self, name: str, max_active_streams: int) -> None:
            self.name = name
            self.max_active_streams = max_active_streams

    fake_xtream = [FakeSource(name, max_streams) for name, max_streams in sources.items()]
    fake_iptv = mocker.MagicMock()
    fake_iptv.xtream = fake_xtream
    fake_iptv.m3u8 = []
    mocker.patch("acere.services.iptv_proxy.pool.pool.settings.iptv", fake_iptv)


def test_check_in_unlimited(mocker: MockerFixture) -> None:
    """When max_active_streams=0, check_in always returns True."""
    _mock_settings_with_sources(mocker, {"unlimited-source": 0})
    pool = IPTVPoolManager(instance_id="test")
    assert pool.check_in("slug-1", "unlimited-source") is True
    assert pool.check_in("slug-2", "unlimited-source") is True
    # No pool should be created for unlimited sources
    assert "unlimited-source" not in pool._source_pools


def test_check_in_with_capacity(mocker: MockerFixture) -> None:
    """When pool has capacity, check_in adds the entry and returns True."""
    _mock_settings_with_sources(mocker, {"limited-source": 2})
    pool = IPTVPoolManager(instance_id="test")
    assert pool.check_in("slug-1", "limited-source") is True
    assert pool.check_in("slug-2", "limited-source") is True
    assert pool._source_pools["limited-source"].active_count == 2


def test_check_in_existing_entry_updates_last_used(mocker: MockerFixture) -> None:
    """Checking in an existing slug should update last_used, not add a duplicate."""
    _mock_settings_with_sources(mocker, {"my-source": 2})
    pool = IPTVPoolManager(instance_id="test")
    pool.check_in("slug-1", "my-source")

    entry = pool._source_pools["my-source"].get_entry("slug-1")
    assert entry is not None
    old_time = entry.date_last_used
    entry.date_last_used = datetime.now(tz=UTC) - timedelta(minutes=5)

    pool.check_in("slug-1", "my-source")
    assert entry.date_last_used > old_time - timedelta(seconds=1)
    assert pool._source_pools["my-source"].active_count == 1


def test_check_in_full_evicts_lru(mocker: MockerFixture) -> None:
    """When pool is full with evictable entries, check_in evicts LRU and succeeds."""
    _mock_settings_with_sources(mocker, {"src": 2})
    pool = IPTVPoolManager(instance_id="test")
    pool.check_in("slug-1", "src")
    pool.check_in("slug-2", "src")

    # Make slug-1 older (LRU candidate)
    entry1 = pool._source_pools["src"].get_entry("slug-1")
    assert entry1 is not None
    entry1.date_last_used = datetime.now(tz=UTC) - timedelta(minutes=10)

    assert pool.check_in("slug-3", "src") is True
    assert pool._source_pools["src"].get_entry("slug-1") is None  # Evicted
    assert pool._source_pools["src"].get_entry("slug-3") is not None


def test_check_in_full_all_locked_returns_false(mocker: MockerFixture) -> None:
    """When pool is full and all entries are locked in, check_in returns False."""
    _mock_settings_with_sources(mocker, {"src": 2})
    pool = IPTVPoolManager(instance_id="test")
    pool.check_in("slug-1", "src")
    pool.check_in("slug-2", "src")

    # Make both entries locked in: old enough and recently used
    now = datetime.now(tz=UTC)
    for key in ["slug-1", "slug-2"]:
        entry = pool._source_pools["src"].get_entry(key)
        assert entry is not None
        entry.date_started = now - timedelta(minutes=10)
        entry.date_last_used = now - timedelta(minutes=1)
        assert entry.check_locked_in() is True

    assert pool.check_in("slug-3", "src") is False
    assert pool._source_pools["src"].active_count == 2


def test_per_source_isolation(mocker: MockerFixture) -> None:
    """Filling one source should not affect another source."""
    _mock_settings_with_sources(mocker, {"src-a": 1, "src-b": 1})
    pool = IPTVPoolManager(instance_id="test")

    pool.check_in("slug-a", "src-a")

    # Make it locked in
    entry_a = pool._source_pools["src-a"].get_entry("slug-a")
    assert entry_a is not None
    now = datetime.now(tz=UTC)
    entry_a.date_started = now - timedelta(minutes=10)
    entry_a.date_last_used = now - timedelta(minutes=1)

    # src-a is full and locked
    assert pool.check_in("slug-a2", "src-a") is False

    # src-b should still work
    assert pool.check_in("slug-b", "src-b") is True


def test_touch_updates_last_used(mocker: MockerFixture) -> None:
    """touch() should update last_used for a tracked entry."""
    _mock_settings_with_sources(mocker, {"src": 2})
    pool = IPTVPoolManager(instance_id="test")
    pool.check_in("slug-1", "src")

    entry = pool._source_pools["src"].get_entry("slug-1")
    assert entry is not None
    entry.date_last_used = datetime.now(tz=UTC) - timedelta(minutes=5)
    old_time = entry.date_last_used

    pool.touch("slug-1")
    assert entry.date_last_used > old_time


def test_touch_noop_for_untracked(mocker: MockerFixture) -> None:
    """touch() should be a no-op for entries not in any pool."""
    _mock_settings_with_sources(mocker, {"src": 2})
    pool = IPTVPoolManager(instance_id="test")
    pool.touch("nonexistent")  # Should not raise


def test_unknown_source_is_unlimited(mocker: MockerFixture) -> None:
    """An unknown source name should be treated as unlimited."""
    _mock_settings_with_sources(mocker, {})
    pool = IPTVPoolManager(instance_id="test")
    assert pool.check_in("slug-1", "unknown-source") is True
    assert "unknown-source" not in pool._source_pools


def test_remove_entry(mocker: MockerFixture) -> None:
    """remove_entry should remove a specific entry from a source pool."""
    _mock_settings_with_sources(mocker, {"src": 3})
    pool = IPTVPoolManager(instance_id="test")
    pool.check_in("slug-1", "src")
    pool.check_in("slug-2", "src")

    assert pool.remove_entry("src", "slug-1") is True
    assert pool._source_pools["src"].active_count == 1
    assert pool.remove_entry("src", "slug-1") is False  # Already removed
    assert pool.remove_entry("nonexistent", "slug-1") is False


def test_get_all_pool_status(mocker: MockerFixture) -> None:
    """get_all_pool_status should return status for all source pools."""
    _mock_settings_with_sources(mocker, {"src-a": 2, "src-b": 2})
    pool = IPTVPoolManager(instance_id="test")
    pool.check_in("slug-1", "src-a")
    pool.check_in("slug-2", "src-b")

    status = pool.get_all_pool_status()
    assert len(status.sources) == 2
    source_names = {s.source_name for s in status.sources}
    assert source_names == {"src-a", "src-b"}

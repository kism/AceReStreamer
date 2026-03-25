"""Tests for BasePoolEntry lock-in mechanism."""

from datetime import UTC, datetime, timedelta

from acere.services.pool.entry import BasePoolEntry


def test_fresh_entry_not_stale() -> None:
    """A freshly created entry should not be stale."""
    entry = BasePoolEntry(key="test-1")
    assert entry.check_if_stale() is False
    assert entry.check_locked_in() is False


def test_new_entry_recently_used_not_stale() -> None:
    """A new entry (< 5 min) that was recently used should not be stale."""
    entry = BasePoolEntry(key="test-2")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=3)
    entry.date_last_used = now - timedelta(minutes=1)
    assert entry.check_if_stale() is False


def test_new_entry_unused_long_is_stale() -> None:
    """A new entry (< 5 min running) unused > 15 min should be stale."""
    entry = BasePoolEntry(key="test-3")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=3)
    entry.date_last_used = now - timedelta(minutes=16)
    assert entry.check_if_stale() is True


def test_old_entry_actively_used_locked_in() -> None:
    """An old entry (> 5 min) recently used should be locked in and not stale."""
    entry = BasePoolEntry(key="test-4")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=10)
    entry.date_last_used = now - timedelta(minutes=1)
    assert entry.check_locked_in() is True
    assert entry.check_if_stale() is False


def test_old_entry_unlocked_and_expired_is_stale() -> None:
    """An old entry that is unlocked and past unlock time should be stale."""
    entry = BasePoolEntry(key="test-5")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=10)
    entry.date_last_used = now - timedelta(minutes=10)
    assert entry.check_locked_in() is False
    assert entry.get_time_until_unlock() < timedelta(seconds=1)
    assert entry.check_if_stale() is True


def test_very_old_entry_long_unused_is_stale() -> None:
    """A very old entry unused for > 15 minutes should be stale."""
    entry = BasePoolEntry(key="test-6")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=30)
    entry.date_last_used = now - timedelta(minutes=20)
    assert entry.check_if_stale() is True


def test_update_last_used() -> None:
    """update_last_used should refresh the timestamp."""
    entry = BasePoolEntry(key="test-7")
    old_time = entry.date_last_used
    # Simulate time passing
    entry.date_last_used = datetime.now(tz=UTC) - timedelta(minutes=5)
    entry.update_last_used()
    assert entry.date_last_used > old_time - timedelta(seconds=1)


def test_not_locked_in_before_lock_in_time() -> None:
    """An entry running less than LOCK_IN_TIME should never be locked in."""
    entry = BasePoolEntry(key="test-8")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=4)
    entry.date_last_used = now - timedelta(seconds=30)
    assert entry.check_running_long_enough_to_lock_in() is False
    assert entry.check_locked_in() is False


def test_lock_in_time_boundary() -> None:
    """An entry exactly at the LOCK_IN_TIME boundary (5 min + 1 sec)."""
    entry = BasePoolEntry(key="test-9")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=5, seconds=1)
    entry.date_last_used = now - timedelta(minutes=5, seconds=1)
    assert entry.check_running_long_enough_to_lock_in() is True
    assert entry.check_if_stale() is True


def test_time_until_unlock_positive_when_locked() -> None:
    """An actively locked entry should have positive time_until_unlock."""
    entry = BasePoolEntry(key="test-10")
    now = datetime.now(tz=UTC)
    entry.date_started = now - timedelta(minutes=10)
    entry.date_last_used = now - timedelta(seconds=30)
    assert entry.check_locked_in() is True
    assert entry.get_time_until_unlock() > timedelta(seconds=0)

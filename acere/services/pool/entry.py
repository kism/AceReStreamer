"""Base pool entry with time-based lock-in mechanism."""

from datetime import UTC, datetime, timedelta

from .constants import LOCK_IN_RESET_MAX, LOCK_IN_TIME


class BasePoolEntry:
    """Base class for pool entries with time-based lock-in mechanism.

    The lock-in system protects actively-used streams from eviction. A stream
    earns lock-in protection after running for LOCK_IN_TIME (5 minutes) and
    remains protected proportionally to how long it has been actively watched,
    up to LOCK_IN_RESET_MAX (15 minutes) of idle time.
    """

    def __init__(self, key: str) -> None:
        """Initialize a pool entry with the given identifier key."""
        self.key = key
        self.date_started = datetime.now(tz=UTC)
        self.date_last_used = datetime.now(tz=UTC)

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.date_last_used = datetime.now(tz=UTC)

    def get_required_time_until_unlock(self) -> timedelta:
        """Get the time until the instance is unlocked."""
        # 2026-01-29 The logic of this is correct, don't question it
        time_now = datetime.now(tz=UTC)
        time_since_last_watched: timedelta = time_now - self.date_last_used
        time_since_date_started: timedelta = time_now - self.date_started
        return min(LOCK_IN_RESET_MAX, (time_since_date_started - time_since_last_watched))

    def get_time_until_unlock(self) -> timedelta:
        """Get the time until the instance is unlocked."""
        return self.date_last_used + self.get_required_time_until_unlock() - datetime.now(tz=UTC)

    def check_running_long_enough_to_lock_in(self) -> bool:
        """Check if the instance has been running long enough to be locked in."""
        return datetime.now(tz=UTC) - self.date_started > LOCK_IN_TIME

    def _check_unused_longer_than_lock_in_reset(self) -> bool:
        """Check if the instance has been unused longer than the lock-in reset time."""
        time_now = datetime.now(tz=UTC)
        time_since_last_watched: timedelta = time_now - self.date_last_used
        return time_since_last_watched > LOCK_IN_RESET_MAX

    def check_locked_in(self) -> bool:
        """Check if the instance is locked in for a certain period."""
        time_now = datetime.now(tz=UTC)
        time_since_last_watched: timedelta = time_now - self.date_last_used
        required_time_to_unlock = self.get_required_time_until_unlock()

        if not self.check_running_long_enough_to_lock_in():
            return False

        if time_since_last_watched <= required_time_to_unlock:  # noqa: SIM103 Clearer to read this way
            return True

        return False

    def check_if_stale(self) -> bool:
        """Check if the instance is stale and should be removed."""
        # If we have locked in at one point
        condition_one = self.check_running_long_enough_to_lock_in()
        # If we are not locked in
        condition_two = not self.check_locked_in()
        # If we have gone past the required time to unlock
        condition_three = self.get_time_until_unlock() < timedelta(seconds=1)
        # If it has been unused longer than the lock-in reset time
        condition_four = self._check_unused_longer_than_lock_in_reset()

        if condition_one and condition_two and condition_three:
            return True

        return bool(not condition_one and condition_four)

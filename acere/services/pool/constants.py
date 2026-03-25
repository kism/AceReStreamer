"""Constants for pool lock-in mechanism."""

from datetime import timedelta

LOCK_IN_TIME: timedelta = timedelta(minutes=5)
LOCK_IN_RESET_MAX: timedelta = timedelta(minutes=15)

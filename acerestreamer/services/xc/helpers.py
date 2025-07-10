"""Helper functions for XC services."""

from datetime import UTC, datetime, timedelta


def get_expiry_date() -> str:
    """Get the expiry date in an epoch string."""
    return str(int(datetime.now(tz=UTC).timestamp() + timedelta(days=365).total_seconds()))  # 1 year from now


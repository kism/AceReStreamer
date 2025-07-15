"""Helpers for XC API response population."""

from datetime import UTC, datetime, timedelta

from pydantic import HttpUrl


def get_expiry_date() -> str:
    """Get the expiry date in an epoch string."""
    return str(int(datetime.now(tz=UTC).timestamp() + timedelta(days=365).total_seconds()))  # 1 year from now


def get_port_and_protocol_from_external_url(external_url: HttpUrl) -> tuple[int, int | None, str]:
    """Extract port and protocol from the external URL."""
    http_port = 80
    https_port: int | None = None
    protocol = external_url.scheme

    if protocol == "https":
        https_port = external_url.port if external_url.port else 443
    elif protocol == "http":
        http_port = external_url.port if external_url.port else 80

    return http_port, https_port, protocol

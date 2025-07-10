"""Helpers for XC API response population."""

from datetime import UTC, datetime, timedelta


def get_expiry_date() -> str:
    """Get the expiry date in an epoch string."""
    return str(int(datetime.now(tz=UTC).timestamp() + timedelta(days=365).total_seconds()))  # 1 year from now


def get_port_and_protocol_from_external_url(external_url: str) -> tuple[int, int | None, str]:
    """Extract port and protocol from the external URL."""
    http_port = 80
    https_port: int | None = None
    protocol = "http"

    if "https://" in external_url:
        https_port = 443
        protocol = "https"
    elif "http://" in external_url:
        http_port = 80
        protocol = "http"

    url_no_scheme = external_url.split("://")[-1]
    if ":" in url_no_scheme:
        port = int(url_no_scheme.split(":")[1].split("/")[0])
        if protocol == "https":
            https_port = port
        elif protocol == "http":
            http_port = port
        port = int(url_no_scheme.split(":")[1].split("/")[0])

    return http_port, https_port, protocol



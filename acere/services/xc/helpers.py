"""Helpers for XC API response population."""

import secrets
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import HTTPException

from acere.instances.config import settings

if TYPE_CHECKING:
    from pydantic import HttpUrl
else:
    HttpUrl = object

XC_USERNAME = "acerestreamer"


def get_expiry_date() -> str:
    """Get the expiry date in an epoch string."""
    return str(int(datetime.now(tz=UTC).timestamp() + timedelta(days=365).total_seconds()))  # 1 year from now


def get_port_and_protocol_from_external_url(
    external_url: HttpUrl,
) -> tuple[int, int | None, str]:
    """Extract port and protocol from the external URL."""
    http_port = 80
    https_port: int | None = None
    protocol = external_url.scheme

    if protocol == "https":
        https_port = external_url.port or 443
    elif protocol == "http":
        http_port = external_url.port or 80

    return http_port, https_port, protocol


def check_xc_auth(username: str, password: str) -> str:
    """Check if the provided username and password are valid, return the password if valid."""
    if username == XC_USERNAME and secrets.compare_digest(password, settings.XC_PASSWORD):
        return password

    raise HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Invalid username or password",
    )

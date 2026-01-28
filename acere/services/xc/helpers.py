"""Helpers for XC API response population."""

from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlmodel import Session

from acere.crud import authenticate_stream_token
from acere.database.init import engine

if TYPE_CHECKING:
    from pydantic import HttpUrl
else:
    HttpUrl = object


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
        https_port = external_url.port if external_url.port else 443
    elif protocol == "http":
        http_port = external_url.port if external_url.port else 80

    return http_port, https_port, protocol


def check_xc_auth(username: str, stream_token: str) -> str:
    """Check if the provided username and password are valid, return stream token if valid."""
    with Session(engine) as session:
        result = authenticate_stream_token(session=session, username=username, stream_token=stream_token)
    if result is not None:
        return result.stream_token

    raise HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Invalid username or password",
    )

"""Nice method to log httpx exceptions."""

from typing import TYPE_CHECKING

import httpx2

if TYPE_CHECKING:
    from logging import Logger as CustomLogger

    from pydantic import HttpUrl
else:
    CustomLogger = object
    HttpUrl = object


def log_http_exception(
    logger: CustomLogger,
    url: HttpUrl | str,
    exception: httpx2.HTTPError,
    message: str = "",
) -> None:
    """Log details of an httpx exception."""
    error_name = type(exception).__name__

    msg = f"httpx {error_name} {message} {url}".replace("  ", " ")
    if isinstance(exception, httpx2.HTTPStatusError):
        msg += f"\nstatus: {exception.response.status_code} {exception.response.reason_phrase}"

    logger.error(msg)

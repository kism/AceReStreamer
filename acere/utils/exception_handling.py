"""Nice method to log aiohttp exceptions."""

from typing import TYPE_CHECKING
from aiohttp import ClientResponseError

if TYPE_CHECKING:
    from logging import Logger as CustomLogger

    from aiohttp import ClientError
    from pydantic import HttpUrl
else:
    CustomLogger = object
    ClientError = object
    HttpUrl = object


def log_aiohttp_exception(logger: CustomLogger, site_url: HttpUrl, exception: ClientError) -> None:
    """Log details of an aiohttp exception."""
    error_name = type(exception).__name__
    error_status = getattr(exception, "status", "N/A")
    error_message = getattr(exception, "message", str(exception))

    msg = f"aiohttp, error scraping: {site_url}\n"
    msg += error_name
    msg += f" status: {error_status}"
    msg += f" message: {error_message}"

    logger.error(msg)

def get_status_of_aiohttp_exception(e: ClientError | TimeoutError)

    if isinstance(e, ClientResponseError):
        status_info = f" (ace status: {e.status} {e.message})"
    elif isinstance(e, TimeoutError):
        status_info = f" (TimeoutError)"
    else:
        status_info = f" (??? {e.__class__.__name__})"

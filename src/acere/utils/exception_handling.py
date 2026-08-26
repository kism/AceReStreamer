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


def _get_client_error_status(e: ClientError) -> str:
    if isinstance(e, ClientResponseError):
        return f"status: {e.status} {e.message}"
    return ""


def log_aiohttp_exception(
    logger: CustomLogger,
    url: HttpUrl | str,
    exception: ClientError | TimeoutError,
    message: str = "",
) -> None:
    """Log details of an aiohttp exception."""
    error_name = type(exception).__name__
    error_status = ""

    if isinstance(exception, ClientError):
        error_status = _get_client_error_status(exception)

    msg = f"aiohttp {error_name} {message} {url}".replace("  ", " ")
    msg += f"\n{error_status}" if error_status else ""

    logger.error(msg)

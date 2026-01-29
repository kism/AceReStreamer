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


def _get_timeout_error_status(e: TimeoutError) -> str:
    return "TimeoutError"


def log_aiohttp_exception(
    logger: CustomLogger,
    url: HttpUrl | str,
    exception: ClientError | TimeoutError,
    message: str = "",
) -> None:
    """Log details of an aiohttp exception."""
    error_name = type(exception).__name__
    error_status = (
        _get_client_error_status(exception)
        if isinstance(exception, ClientError)
        else _get_timeout_error_status(exception)
    )
    error_message = getattr(exception, "message", None)

    msg = f"aiohttp: {message} {url}\n".replace("  ", " ")
    msg += error_name
    msg += f" status: {error_status}"
    msg += f" message: {error_message}" if error_message else ""

    logger.error(msg)

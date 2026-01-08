"""Nice method to log aiohttp exceptions."""

from logging import Logger as CustomLogger

from aiohttp import ClientError
from pydantic import HttpUrl

# from acere.utils.logger import CustomLogger


def log_aiohttp_exception(logger: CustomLogger, site_url: HttpUrl, exception: ClientError) -> None:
    """Log details of an aiohttp exception."""
    error_name = type(exception).__name__
    error_status = getattr(exception, "status", "N/A")
    error_code = getattr(exception, "code", "N/A")
    error_message = getattr(exception, "message", str(exception))

    msg = f"aiohttp, error scraping: {site_url}\n"
    msg += error_name
    if error_status != error_code:
        msg += f" code: {error_code}, {error_status}"
    else:
        msg += f" code: {error_status}"

    msg += f" message: {error_message}"

    logger.error(msg)

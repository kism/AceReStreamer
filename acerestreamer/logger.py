"""Setup the logger functionality for acerestreamer."""

import logging
import typing
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import cast

from colorama import Fore, init

init(autoreset=True)

COLOURS = {
    "TRACE": Fore.CYAN,
    "DEBUG": Fore.GREEN,
    "INFO": Fore.WHITE,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED,
}

LOG_LEVELS = [
    "TRACE",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]  # Valid str logging levels.
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"  # This is the logging message format that I like.
LOG_FORMAT_CONSOLE = "%(levelname)s:%(message)s"
TRACE_LEVEL_NUM = 5


class ColorFormatter(logging.Formatter):
    """Formatter for coloring the log messages, this is ONLY for console output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log message."""
        if isinstance(record.msg, tuple):
            record.msg = "  ".join(map(str, record.msg))

        elif record.msg is None:
            record.msg = "<NoneType>"

        elif isinstance(record.msg, list):
            record.msg = "  \n".join(map(str, record.msg))

        if record.levelno == logging.INFO:  # No need to colourise/format INFO messages
            return f"{record.getMessage()}"

        colour = COLOURS.get(record.levelname, "")
        if colour:
            record.name = f"{colour}{record.name}"
            record.levelname = f"{colour}{record.levelname}"
            record.msg = f"{colour}{record.msg}"
        return super().format(record)


class CustomLogger(logging.Logger):
    """Custom logger to appease mypy."""

    def trace(self, message: typing.Any, *args: typing.Any, **kws: typing.Any) -> None:  # noqa: ANN401 # No other way to do this
        """Create logger level for trace."""
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            # Yes, logger takes its '*args' as 'args'.
            self._log(TRACE_LEVEL_NUM, message, args, **kws)


logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
logging.setLoggerClass(CustomLogger)

# This is where we log to in this module, following the standard of every module.
# I don't use the function so we can have this at the top
logger = cast("CustomLogger", logging.getLogger(__name__))

# In flask the root logger doesn't have any handlers, its all in app.logger
# root_logger : root,
# app.logger  : root, acerestreamer,
# logger      : root, acerestreamer, acerestreamer.module_name,
# The issue is that waitress, werkzeug (any any other modules that log) will log separately.
# The aim is, remove the default handler from the flask App and create one on the root logger to apply config to all.


# Pass in the whole app object to make it obvious we are configuring the logger object within the app object.
def setup_logger(
    log_level: str | int = logging.INFO,
    log_path: Path | str = "",  # We don't use nonetype due to compatibility with TOML
    in_loggers: list[logging.Logger] | None = None,
    *,
    include_root_logger: bool = True,
    console_only: bool = False,
) -> None:
    """Setup the logger, set configuration per logging_conf.

    Args:
        log_level: Logging level to set.
        log_path: Path to log to.
        in_loggers: Loggers to configure, includes root logger by default.
        include_root_logger: Include the root logger in the configuration, false for testing.
        console_only: If true, load the settings for CLI mode.
    """
    if in_loggers is None:  # Fun python things
        in_loggers = []

    if include_root_logger:  # in_logger, used to exclude the root logger in pytest
        in_loggers.append(logging.getLogger())  # pragma: no cover # get the root logger

    for in_logger in in_loggers:
        # If the logger doesn't have a console handler (root logger doesn't by default)
        if not _has_console_handler(in_logger):
            _add_console_handler(in_logger, console_only=console_only)

        _set_log_level(in_logger, log_level)

        # If we are logging to a file
        if not _has_file_handler(in_logger) and not isinstance(log_path, str):
            _add_file_handler(in_logger, log_path)

        # Configure modules that are external and have their own loggers
        logging.getLogger("waitress").setLevel(logging.INFO)  # Prod web server, info has useful info.
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)  # Only will be used in dev, debug logs incoming requests.
        logging.getLogger("urllib3").setLevel(logging.WARNING)  # Suppress urllib3 warnings, we don't care about them.

        logger.debug("Logger configuration set!")


def get_logger(name: str) -> CustomLogger:
    """Get a logger with the name provided."""
    return cast("CustomLogger", logging.getLogger(name))


def _has_file_handler(in_logger: logging.Logger) -> bool:
    """Check if logger has a file handler."""
    return any(isinstance(handler, logging.FileHandler) for handler in in_logger.handlers)


def _has_console_handler(in_logger: logging.Logger) -> bool:
    """Check if logger has a console handler."""
    return any(isinstance(handler, logging.StreamHandler) for handler in in_logger.handlers)


def _add_console_handler(in_logger: logging.Logger, *, console_only: bool = False) -> None:
    """Add a console handler to the logger."""
    log_fromat = LOG_FORMAT_CONSOLE if console_only else LOG_FORMAT

    formatter = ColorFormatter(log_fromat) if console_only else logging.Formatter(log_fromat)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    in_logger.addHandler(console_handler)


def _set_log_level(in_logger: logging.Logger, log_level: int | str) -> None:
    """Set the log level of the logger."""
    if isinstance(log_level, str):
        log_level = log_level.upper()
        if log_level not in LOG_LEVELS:
            in_logger.setLevel("INFO")
            logger.warning(
                "❗ Invalid logging level: %s, defaulting to INFO",
                log_level,
            )
        else:
            in_logger.setLevel(log_level)
            logger.trace("Set log level: %s", log_level)
            logger.debug("Set log level: %s", log_level)
    else:
        in_logger.setLevel(log_level)


def _add_file_handler(in_logger: logging.Logger, log_path: Path) -> None:
    """Add a file handler to the logger."""
    try:
        file_handler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=5)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc
    except PermissionError as exc:
        err = f"The user running this does not have access to the file: {log_path}"
        raise PermissionError(err) from exc

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    in_logger.addHandler(file_handler)
    logger.info("Logging to file: %s", log_path)

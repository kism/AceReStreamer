"""Setup the logger functionality."""

import logging
from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Self, cast

from pydantic import BaseModel, field_validator, model_validator
from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.theme import Theme

LOG_LEVELS = [
    "TRACE",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]  # Valid str logging levels.

# This is the logging message format that I like.
SIMPLE_LOG_FORMAT = "%(levelname)s:%(message)s"
SIMPLE_LOG_FORMAT_DEBUG = "%(levelname)s:%(name)s:%(message)s"
TRACE_LEVEL_NUM = 5

MIN_LOG_LEVEL_INT = 0
MAX_LOG_LEVEL_INT = 50

FILE_HANDLER_MAX_BYTES = 1000000  # 1MB
FILE_HANDLER_BACKUP_COUNT = 5


class LoggingConf(BaseModel):
    """Logging configuration definition."""

    level: str | int = "INFO"
    level_http: str | int = "WARNING"
    path: Path | None = None
    simple: bool = False

    @model_validator(mode="after")
    def validate_vars(self) -> Self:
        """Validate the logging level."""

        def process_level(level: str | int) -> str | int:
            if isinstance(level, int):
                if level < MIN_LOG_LEVEL_INT or level > MAX_LOG_LEVEL_INT:
                    msg = f"Invalid logging level {level}, must be between {MIN_LOG_LEVEL_INT} and {MAX_LOG_LEVEL_INT}."
                    logger.warning(msg)
                    logger.warning("Defaulting logging level to 'INFO'.")
                    level = "INFO"
            else:
                level = level.strip().upper()
                if level not in LOG_LEVELS:
                    msg = f"Invalid logging level '{level}', must be one of {', '.join(LOG_LEVELS)}"
                    logger.warning(msg)
                    logger.warning("Defaulting logging level to 'INFO'.")
                    level = "INFO"

            return level

        self.level = process_level(self.level)
        self.level_http = process_level(self.level_http)

        return self

    @field_validator("path", mode="before")
    def set_path(cls, value: str | None) -> Path | None:
        """Set the path to a slugified version."""
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

        if value == "":
            return None

        return Path(value)

    def setup_verbosity_cli(self, verbosity: int) -> None:
        """Setup the logger from verbosity count from CLI."""
        if verbosity >= 2:  # noqa: PLR2004 Magic number makes sense
            self.level = TRACE_LEVEL_NUM
        elif verbosity == 1:
            self.level = logging.DEBUG
        else:
            self.level = logging.INFO


class CustomLogger(logging.Logger):
    """Custom logger to appease mypy."""

    def trace(self, message: Any, *args: Any, **kws: Any) -> None:  # noqa: ANN401 Logging handles this
        """Create logger level for trace."""
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            # Yes, logger takes its '*args' as 'args'.
            self._log(TRACE_LEVEL_NUM, message, args, **kws)


logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
logging.setLoggerClass(CustomLogger)

# This is where we log to in this module, following the standard of every module.
# I don't use the function so we can have this at the top
logger = cast("CustomLogger", logging.getLogger(__name__))


# Pass in the whole app object to make it obvious we are configuring the logger object within the app object.
def setup_logger(
    settings: LoggingConf | None = None,
    in_logger: logging.Logger | str | None = None,
) -> None:
    """Setup the logger, set configuration per logging_config."""
    if settings is None:
        settings = LoggingConf()

    if isinstance(in_logger, str):
        in_logger = logging.getLogger(in_logger)

    loggers = list(logging.Logger.manager.loggerDict.keys())
    logger.trace("Existing loggers: %s", ", ".join(loggers) if loggers else "None")

    if not in_logger:  # in_logger should only exist when testing with PyTest.
        in_logger = logging.getLogger()  # Get the root logger

    # If the logger doesn't have a console handler (root logger doesn't by default)
    if not any(isinstance(handler, (RichHandler, StreamHandler)) for handler in in_logger.handlers):
        _add_console_handler(settings, in_logger)

    _set_log_level(settings, in_logger)

    # If we are logging to a file
    if not any(isinstance(handler, FileHandler) for handler in in_logger.handlers) and settings.path:
        _add_file_handler(in_logger, settings.path)

    logging.getLogger("uvicorn").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").propagate = False
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.ERROR)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("python_multipart").setLevel(TRACE_LEVEL_NUM)
    logging.getLogger("python_multipart.multipart").setLevel(TRACE_LEVEL_NUM)

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.propagate = False
    access_logger.setLevel(settings.level_http)

    logger.debug("Logger configuration set!")


def get_logger(name: str) -> CustomLogger:
    """Get a logger with the name provided."""
    return cast("CustomLogger", logging.getLogger(name))


def _add_console_handler(
    settings: LoggingConf,
    in_logger: logging.Logger,
) -> None:
    """Add a console handler to the logger."""
    if not settings.simple:
        console = Console(theme=Theme({"logging.level.trace": "dim"}))
        rich_handler = RichHandler(
            console=console,
            show_time=False,
            rich_tracebacks=True,
            highlighter=NullHighlighter(),
        )
        in_logger.addHandler(rich_handler)
    else:
        console_handler = StreamHandler()
        if _get_log_level_int(settings.level) <= TRACE_LEVEL_NUM:
            formatter = logging.Formatter(SIMPLE_LOG_FORMAT_DEBUG)
        else:
            formatter = logging.Formatter(SIMPLE_LOG_FORMAT)

        console_handler.setFormatter(formatter)
        in_logger.addHandler(console_handler)


def _get_log_level_int(level: str | int) -> int:
    """Get the log level as an int."""
    if isinstance(level, int):
        return level

    level = level.upper()
    if level == "TRACE":
        return TRACE_LEVEL_NUM
    return getattr(logging, level, logging.INFO)


def _set_log_level(
    settings: LoggingConf,
    in_logger: logging.Logger,
) -> None:
    """Set the log level of the logger."""
    log_level = settings.level
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
            logger.debug("Set log level: %s", log_level)
    else:
        in_logger.setLevel(log_level)


def _add_file_handler(in_logger: logging.Logger, log_path: Path) -> None:
    """Add a file handler to the logger."""
    try:
        file_handler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=3)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc
    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + str(log_path.resolve())
        raise PermissionError(err) from exc

    formatter = logging.Formatter(SIMPLE_LOG_FORMAT_DEBUG)
    file_handler.setFormatter(formatter)
    in_logger.addHandler(file_handler)
    logger.info("Logging to file: %s", log_path)

import logging
from typing import TYPE_CHECKING

import pytest

from acere.utils.logger import TRACE_LEVEL_NUM, LoggingConf, _add_file_handler, get_logger

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


def test_logger_file_handler(tmp_path: Path) -> None:
    logger = get_logger("test_logger")
    log_file = tmp_path / "test.log"

    _add_file_handler(logger, log_path=log_file)


def test_logger_file_handler_is_directory(tmp_path: Path) -> None:
    logger = get_logger("test_logger_dir")
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()

    with pytest.raises(IsADirectoryError):
        _add_file_handler(logger, log_path=log_dir)


def test_logging_conf() -> None:
    LoggingConf()


def test_logging_conf_level_too_high(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING"):
        LoggingConf(level=100)

    assert "Invalid logging level 100" in caplog.text


def test_logging_level_invalid(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING"):
        LoggingConf(level="Foo")

    assert "Invalid logging level 'FOO'" in caplog.text


def test_verbosity_cli() -> None:
    conf = LoggingConf()
    conf.setup_verbosity_cli(0)
    assert conf.level == logging.INFO
    conf.setup_verbosity_cli(1)
    assert conf.level == logging.DEBUG

    conf.setup_verbosity_cli(2)
    assert conf.level == TRACE_LEVEL_NUM

def test_path_wraps_to_none() -> None:
    conf = LoggingConf(path="") # type: ignore[arg-type]

    assert conf.path is None

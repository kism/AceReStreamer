"""Logger unit tests."""

import logging

import pytest

import acerestreamer.logger
from acerestreamer.logger import _add_file_handler, _set_log_level, setup_logger


@pytest.fixture
def logger():
    """Logger to use in unit tests, including cleanup."""
    logger = logging.getLogger("TEST_LOGGER")

    assert len(logger.handlers) == 0  # Check the logger has no handlers

    yield logger

    # Reset the test object since it will persist.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_logging_permissions_error(logger, tmp_path, mocker):
    """Test logging, mock a permission error."""

    mock_open_func = mocker.mock_open(read_data="")
    mock_open_func.side_effect = PermissionError("Permission denied")

    mocker.patch("builtins.open", mock_open_func)

    # TEST: That a permissions error is raised when open() results in a permissions error.
    with pytest.raises(PermissionError):
        _add_file_handler(logger, str(tmp_path))


def test_config_logging_to_dir(logger, tmp_path):
    """TEST: Correct exception is caught when you try log to a folder."""

    with pytest.raises(IsADirectoryError):
        _add_file_handler(logger, tmp_path)


def test_handler_console_added(logger, app):
    """Test logging console handler."""
    logging_conf = {
        "log_level": "INFO",
        "log_path": "",
        "in_loggers": [logger],
        "include_root_logger": False,
    }

    acerestreamer.logger.setup_logger(**logging_conf)
    assert len(logger.handlers) == 1

    # TEST: Still only one handler
    acerestreamer.logger.setup_logger(**logging_conf)
    assert len(logger.handlers) == 1


def test_handler_file_added(logger, tmp_path, app):
    """Test logging file handler."""
    logging_conf = {
        "log_level": "INFO",
        "log_path": tmp_path / "test.log",
        "in_loggers": [logger],
        "include_root_logger": False,
    }

    acerestreamer.logger.setup_logger(**logging_conf)
    assert len(logger.handlers) == 2  # noqa: PLR2004 A console and a file handler are expected

    # TEST: Still two handlers
    acerestreamer.logger.setup_logger(**logging_conf)
    assert len(logger.handlers) == 2  # noqa: PLR2004 A console and a file handler are expected


def test_no_loggers_supplied():
    """Test if no loggers supplied, root logger is used."""

    # This is just for coverage
    setup_logger(include_root_logger=False)

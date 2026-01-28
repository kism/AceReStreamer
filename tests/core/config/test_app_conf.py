import logging
from typing import TYPE_CHECKING

from acere.core.config import AppConf

if TYPE_CHECKING:
    import pytest
else:
    pytest = object


def test_app_conf_loads_default_config(caplog: pytest.LogCaptureFixture) -> None:
    """Test that AppConf loads the default configuration correctly."""
    with caplog.at_level(logging.WARNING):
        AppConf()

    assert caplog.records == []  # No warnings should be logged during default load


def test_max_streams_values(caplog: pytest.LogCaptureFixture) -> None:
    """Test that max_streams values are set and retrieved correctly."""
    warnings_so_far: list[str] = []

    n_streams = 0
    with caplog.at_level(logging.WARNING):
        conf = AppConf(ace_max_streams=n_streams)
    assert len(caplog.records) == 1
    assert conf.ace_max_streams == 4  # Default should be applied
    warnings_so_far.append(caplog.records[0].message)

    caplog.clear()

    n_streams = 11
    with caplog.at_level(logging.WARNING):
        AppConf(ace_max_streams=n_streams)
    assert len(caplog.records) == 1
    warnings_so_far.append(caplog.records[0].message.replace(str(n_streams), "X"))

    caplog.clear()

    n_streams = 21
    with caplog.at_level(logging.WARNING):
        AppConf(ace_max_streams=n_streams)
    assert len(caplog.records) == 1
    warnings_so_far.append(caplog.records[0].message.replace(str(n_streams), "X"))

    assert len(set(warnings_so_far)) == 3  # Ensure all three warnings are unique

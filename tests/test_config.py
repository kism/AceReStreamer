from pathlib import Path

import pytest

from acestreamwebplayer.config import load_config


def test_invalid_message(get_test_config):
    """Test invalid message."""
    with pytest.raises(ValueError, match="AppConfDef: my_message cannot be empty"):
        get_test_config("config_app_message_invalid.toml")


def test_load_missing_config(tmp_path):
    """Test loading a missing config file."""
    missing_config = Path(tmp_path) / "missing_config.toml"
    config = load_config(missing_config)
    config.write_config(missing_config)

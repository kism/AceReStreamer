import logging
from typing import TYPE_CHECKING

from acere.core.config import AceReStreamerConf

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
else:
    pytest = object
    Path = object


def test_force_load_config_file_existing(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test loading a config file that exists."""
    # Create a temporary config file
    generated_config = AceReStreamerConf.force_load_defaults()
    generated_config.app.ace_max_streams = 8
    generated_config.scraper.playlist_name = "pytest"
    config_path = tmp_path / "test_config.json"

    config_path.write_text(generated_config.model_dump_json(indent=4))

    config = AceReStreamerConf.force_load_config_file(config_path)

    # Verify the loaded values match what we put in the file
    assert config.app.ace_max_streams == 8
    assert config.scraper.playlist_name == "pytest"

    config_path.unlink()
    with caplog.at_level(logging.WARNING):
        config.write_config(config_path)

    assert "Writing fresh config file at" in caplog.text


def test_force_load_config_file_nonexistent(tmp_path: Path) -> None:
    """Test loading a config file that doesn't exist returns defaults."""
    # Create a path to a file that doesn't exist
    nonexistent_path = tmp_path / "nonexistent_config.json"
    assert not nonexistent_path.exists()

    # Load config with non-existent file
    config = AceReStreamerConf.force_load_config_file(nonexistent_path)

    # Should return default config
    assert config.app.ace_max_streams == 4
    assert config.scraper.playlist_name == "acerestreamer"
    assert config.ENVIRONMENT == "local"

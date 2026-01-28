import logging
from typing import TYPE_CHECKING

from pydantic import HttpUrl

from acere.core.config import (
    AceReStreamerConf,
    EPGInstanceConf,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
else:
    pytest = object
    Path = object


def test_add_epg() -> None:
    """Test adding an EPG source."""
    config = AceReStreamerConf.force_load_defaults()
    initial_count = len(config.epgs)

    new_epg = EPGInstanceConf(format="xml.gz", url=HttpUrl("http://example.com/epg.xml.gz"))
    config.add_epg(new_epg)

    assert len(config.epgs) == initial_count + 1
    assert config.epgs[-1].url == new_epg.url


def test_add_duplicate_epg_updates() -> None:
    """Test that adding a duplicate EPG updates the existing one."""
    config = AceReStreamerConf.force_load_defaults()

    new_epg = EPGInstanceConf(format="xml.gz", url=HttpUrl("http://example.com/duplicate.xml.gz"))
    config.add_epg(new_epg)
    initial_count = len(config.epgs)

    # Try to add the same EPG again (same URL)
    duplicate_epg = EPGInstanceConf(format="xml", url=HttpUrl("http://example.com/duplicate.xml.gz"))
    config.add_epg(duplicate_epg)

    # Should not add a new EPG, count should remain the same
    assert len(config.epgs) == initial_count


def test_remove_epg() -> None:
    """Test removing an EPG source."""
    config = AceReStreamerConf.force_load_defaults()

    new_epg = EPGInstanceConf(format="xml.gz", url=HttpUrl("http://example.com/remove.xml.gz"))
    config.add_epg(new_epg)
    initial_count = len(config.epgs)

    # Get the slug of the EPG we just added
    epg_slug = new_epg.slug
    success = config.remove_epg(epg_slug)

    assert success is True
    assert len(config.epgs) == initial_count - 1


def test_remove_nonexistent_epg() -> None:
    """Test removing an EPG that doesn't exist."""
    config = AceReStreamerConf.force_load_defaults()

    success = config.remove_epg("nonexistent-slug")

    assert success is False


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
    assert config.app.authentication_enabled is True
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
    assert config.app.authentication_enabled is True
    assert config.app.ace_max_streams == 4
    assert config.scraper.playlist_name == "acerestreamer"
    assert len(config.epgs) == 0
    assert config.ENVIRONMENT == "local"

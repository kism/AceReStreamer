from pathlib import Path

from acestreamwebplayer.config import load_config


def test_load_missing_config(tmp_path):
    """Test loading a missing config file."""
    missing_config = Path(tmp_path) / "missing_config.toml"
    config = load_config(missing_config)
    config.write_config(missing_config)

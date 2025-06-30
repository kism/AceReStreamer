from pathlib import Path

from acerestreamer.config import AceReStreamerConf


def test_load_missing_config(tmp_path):
    """Test loading a missing config file."""
    missing_config = Path(tmp_path) / "missing_config.json"
    config = AceReStreamerConf.load_config(missing_config)
    config.write_config(missing_config)

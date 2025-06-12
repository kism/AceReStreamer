"""Flask helpers for AceReStreamer."""

from pathlib import Path
from typing import Any, cast

from flask import Flask, current_app

from .config import load_config


class FlaskAceReStreamer(Flask):
    """Extend flask to add out config object to the app object."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Extend flask to add out config object to the app object."""
        super().__init__(*args, **kwargs)
        self.aw_conf = load_config(Path(self.instance_path) / "config.toml")
        self.aw_conf.write_config(Path(self.instance_path) / "config.toml")


def get_current_app() -> FlaskAceReStreamer:
    """Get the current app object."""
    return cast("FlaskAceReStreamer", current_app)

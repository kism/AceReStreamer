"""Flask helpers for AcestreamWebplayer."""

from pathlib import Path
from typing import Any, cast

from flask import Flask, current_app

from .config import load_config


class FlaskAcestreamWebplayer(Flask):
    """Extend flask to add out config object to the app object."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Extend flask to add out config object to the app object."""
        super().__init__(*args, **kwargs)
        self.aw_conf = load_config(Path(self.instance_path) / "config.toml")
        self.aw_conf.write_config(Path(self.instance_path) / "config.toml")


def get_current_app() -> FlaskAcestreamWebplayer:
    """Get the current app object."""
    return cast("FlaskAcestreamWebplayer", current_app)

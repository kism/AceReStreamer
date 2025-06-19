"""Blueprint for EPG Endpoints."""

from pathlib import Path

from flask import Blueprint

from .epg import EPGHandler
from .flask_helpers import get_current_app

current_app = get_current_app()

bp = Blueprint("acerestreamer_scraper", __name__, url_prefix="/epg")

epg_handler = EPGHandler(epg_conf_list=[])


def start_epg_handler() -> None:
    """Start the EPG handler with the provided URLs."""
    global epg_handler  # noqa: PLW0603 Hard to avoid
    instance_path = Path(current_app.instance_path)
    epg_handler = EPGHandler(epg_conf_list=current_app.aw_conf.epgs, instance_path=instance_path)

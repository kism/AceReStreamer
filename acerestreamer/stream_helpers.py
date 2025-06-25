"""Helpers for Stream Parsing."""

from flask import current_app

from .flask_helpers import aw_conf
from .logger import get_logger

logger = get_logger(__name__)

ACE_CONTENT_PATH = "/ace/c/"


def replace_m3u_sources(m3u_content: str) -> str:
    """Replace Ace Stream sources in M3U content with a specified external server URL."""
    if not m3u_content:
        logger.warning("Received empty M3U content for replacement.")
        return ""

    def process_line(line: str) -> str:
        line_stripped = line.strip()
        if ACE_CONTENT_PATH in line and line_stripped.startswith(aw_conf.app.ace_address):
            return line_stripped.replace(aw_conf.app.ace_address, current_app.config["SERVER_NAME"])
        return line_stripped

    return "\n".join(process_line(line) for line in m3u_content.splitlines())

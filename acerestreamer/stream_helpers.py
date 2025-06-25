"""Helpers for Stream Parsing."""

from flask import current_app

from .flask_helpers import aw_conf


def replace_m3u_sources(m3u_content: str) -> str:
    """Replace Ace Stream sources in M3U content with a specified external server URL."""
    lines_new = []

    for line in m3u_content.splitlines():
        line_temp = line.strip()
        if "/ace/c/" in line and line_temp.startswith(aw_conf.app.ace_address):
            line_temp = line_temp.replace(aw_conf.app.ace_address, current_app.config["SERVER_NAME"])

        lines_new.append(line_temp)

    return "\n".join(lines_new)

"""Helpers for Stream Parsing."""

from .flask_helpers import get_current_app

current_app = get_current_app()


def replace_m3u_sources(m3u_content: str) -> str:
    """Replace Ace Stream sources in M3U content with a specified external server URL."""
    lines_new = []

    for line in m3u_content.splitlines():
        line_temp = line.strip()
        if "/ace/c/" in line and line_temp.startswith(current_app.aw_conf.app.ace_address):
            line_temp = line_temp.replace(current_app.aw_conf.app.ace_address, current_app.config["SERVER_NAME"])

        lines_new.append(line_temp)

    return "\n".join(lines_new)

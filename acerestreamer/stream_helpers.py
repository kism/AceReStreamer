"""Helpers for Stream Parsing."""

import re

from .ace_pool import AcePool
from .flask_helpers import get_current_app

current_app = get_current_app()


def replace_m3u_sources(m3u_content: str, path: str, ace_pool: AcePool) -> str:
    """Replace Ace Stream sources in M3U content with a specified external server URL."""
    lines_new = []

    content_path_known = False
    for line in m3u_content.splitlines():
        line_temp = line.strip()
        if "/ace/c/" in line:
            for address in current_app.aw_conf.app.ace_addresses:
                if line_temp.startswith(address):
                    line_temp = line_temp.replace(address, current_app.config["SERVER_NAME"])

            if not content_path_known:
                current_content_identifier = re.search(r"/ace/c/([a-f0-9]+)", line_temp)

                content_path_known = bool(current_content_identifier)

                if current_content_identifier:
                    ace_pool.set_content_path(ace_id=path, content_path=current_content_identifier.group(1))

        lines_new.append(line_temp)

    return "\n".join(lines_new)

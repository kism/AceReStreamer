"""Helpers for Stream Parsing."""

from typing import TYPE_CHECKING

from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pydantic import HttpUrl
else:
    HttpUrl = object

logger = get_logger(__name__)

CONTENT_PATHS = ["/ace/c/", "/hls/c/", "/hls/m/"]


def replace_hls_m3u_sources(
    m3u_content: str,
    ace_address: HttpUrl,
    server_name: HttpUrl,
    token: str,
) -> str:
    """Replace Ace Stream sources in M3U content with a specified external server URL."""
    if not m3u_content:
        logger.warning("Received empty M3U content for replacement.")
        return ""

    def process_line(line: str) -> str:
        line_stripped = line.strip()

        if "#EXT-X-MEDIA:URI=" in line_stripped:  # Avoid whatever this is, seems to bork VLC
            return ""

        if any(path in line_stripped for path in CONTENT_PATHS):
            # Replace the Ace Stream address with the server name
            wip_line = line_stripped.replace(ace_address.encoded_string(), server_name.encoded_string())
            if token != "":
                wip_line += f"?token={token}"
            line_stripped = wip_line
        return line_stripped

    return "\n".join(process_line(line) for line in m3u_content.splitlines())

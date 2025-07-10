"""Helpers for Stream Parsing."""

from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

CONTENT_PATHS = ["/ace/c/", "/hls/c/", "/hls/m/"]


def replace_m3u_sources(m3u_content: str, ace_address: str, server_name: str) -> str:
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
            return line_stripped.replace(ace_address, server_name)
        return line_stripped

    return "\n".join(process_line(line) for line in m3u_content.splitlines())

"""Helpers for Stream Parsing."""

from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

ACE_CONTENT_PATH = "/ace/c/"


def replace_m3u_sources(m3u_content: str, ace_address: str, server_name: str) -> str:
    """Replace Ace Stream sources in M3U content with a specified external server URL."""
    if not m3u_content:
        logger.warning("Received empty M3U content for replacement.")
        return ""

    def process_line(line: str) -> str:
        line_stripped = line.strip()
        if ACE_CONTENT_PATH in line and line_stripped.startswith(ace_address):
            return line_stripped.replace(ace_address, server_name)
        return line_stripped

    return "\n".join(process_line(line) for line in m3u_content.splitlines())

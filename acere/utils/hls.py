"""Helpers for Stream Parsing."""

from typing import TYPE_CHECKING

from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pydantic import HttpUrl
else:
    HttpUrl = object

logger = get_logger(__name__)

_CONTENT_PATHS = ["/ace/c/", "/hls/c/", "/hls/m/"]


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

        if any(path in line_stripped for path in _CONTENT_PATHS):
            # Replace the Ace Stream address with the server name
            wip_line = line_stripped.replace(ace_address.encoded_string(), server_name.encoded_string())
            if token != "":
                wip_line += f"?token={token}"
            line_stripped = wip_line
        return line_stripped

    return "\n".join(process_line(line) for line in m3u_content.splitlines())


def get_last_m3u8_segment_url(m3u_content: str) -> str | None:
    """Get the last segment URL from an M3U8 playlist."""
    if not m3u_content:
        return None

    lines = m3u_content.strip().splitlines()
    for line in reversed(lines):
        line_stripped = line.strip()
        if line_stripped and line_stripped.startswith("http"):
            return line_stripped

    logger.warning("No segment URL found in M3U content.")
    return None


def rewrite_iptv_hls_segments(
    m3u_content: str,
    slug: str,
    server_name: str,
) -> str:
    """Rewrite segment URLs in an HLS playlist to route through the IPTV proxy.

    Converts absolute/relative segment URLs to:
    {server_name}/hls/seg/{slug}/{segment_path}

    No token is appended — segments are served without auth for nginx caching.
    """
    if not m3u_content:
        logger.warning("Received empty M3U content for IPTV rewrite.")
        return ""

    server_name = server_name.rstrip("/")

    lines = m3u_content.splitlines()
    result_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            result_lines.append(stripped)
        elif stripped.startswith("http"):
            # Absolute URL — extract the path from the URL
            from urllib.parse import urlparse  # noqa: PLC0415

            segment_path = urlparse(stripped).path.lstrip("/")
            result_lines.append(f"{server_name}/hls/seg/{slug}/{segment_path}")
        elif stripped.startswith("/"):
            # Root-relative URL — strip leading slash
            result_lines.append(f"{server_name}/hls/seg/{slug}/{stripped.lstrip('/')}")
        elif stripped:
            # Relative URL — use as-is for the segment name
            result_lines.append(f"{server_name}/hls/seg/{slug}/{stripped}")
        else:
            result_lines.append(stripped)

    return "\n".join(result_lines)

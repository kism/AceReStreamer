"""Helper functions for AceStream scraper services."""

from typing import TYPE_CHECKING

from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pydantic import HttpUrl

    from .models import FoundAceStream
else:
    HttpUrl = object
    FoundAceStream = object

logger = get_logger(__name__)


def create_unique_stream_list(
    streams: list[FoundAceStream],
) -> dict[str, FoundAceStream]:
    """Create a unique list of FoundAceStream objects based on their infohash and content_id."""
    found_streams: dict[str, FoundAceStream] = {}

    for stream in streams:
        if stream.content_id == "":
            continue

        if stream.content_id in found_streams:
            existing_stream = found_streams[stream.content_id]
            existing_stream.site_names.extend(stream.site_names)

            if existing_stream.tvg_logo == "" and stream.tvg_logo != "":
                existing_stream.tvg_logo = stream.tvg_logo

            # Prefer titles with brackets for country code
            if existing_stream.title != stream.title:
                if not any(char in existing_stream.title for char in ["[", "]"]):
                    existing_stream.title = stream.title
                else:
                    logger.warning(
                        "Duplicate content_id found with different titles: %s vs %s",
                        existing_stream.title,
                        stream.title,
                    )

        else:
            found_streams[stream.content_id] = stream

    return found_streams


def create_extinf_line(stream: FoundAceStream, tvg_url_base: HttpUrl | None, token: str = "") -> str:
    """Create an M3U EXTINF line for a given FoundAceStream object."""
    token_str = "" if token == "" else f"?token={token}"

    final_url_base = None
    if tvg_url_base is not None:
        final_url_base = tvg_url_base.encoded_string().removesuffix("/")
    out = [
        "#EXTINF:-1",
        f'tvg-logo="{final_url_base}/{stream.tvg_logo}{token_str}"' if stream.tvg_logo and final_url_base else "",
        f'tvg-id="{stream.tvg_id}"',
        f'group-title="{stream.group_title}"',
        f'x-last-found="{stream.last_found_time}"',
    ]

    return " ".join(part for part in out if part) + f", {stream.title}\n"

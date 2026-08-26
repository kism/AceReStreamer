"""Helper functions for AceStream scraper services."""

from typing import TYPE_CHECKING

import aiohttp

from acere.instances.config import settings
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
        if stream.content_id == "":  # Right now this only happens in adhoc mode
            continue

        if stream.content_id in found_streams:
            existing_stream = found_streams[stream.content_id]
            existing_stream.sites_found_on.extend(stream.sites_found_on)

            if not existing_stream.tvg_logo and stream.tvg_logo:
                existing_stream.tvg_logo = stream.tvg_logo

            if existing_stream.infohash is None and stream.infohash is not None:
                existing_stream.infohash = stream.infohash

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


async def get_content_id_from_infohash_acestream_api(infohash: str) -> str:
    """Populate the mapping from th Ace API from infohash, returning the content ID."""
    logger.info("Populating missing content ID for infohash %s", infohash)
    content_id = ""
    url = f"{settings.app.ace_address}server/api?api_version=3&method=get_content_id&infohash={infohash}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except aiohttp.ClientConnectorError:
        logger.error(
            "Connection error while trying to reach Ace Stream API at %s",
            url,
        )
        return content_id
    except (aiohttp.ClientError, ValueError) as e:
        error_short = type(e).__name__
        logger.error(
            "%s Failed to fetch content ID for infohash %s",
            error_short,
            infohash,
        )
        return content_id

    if data.get("result", {}).get("content_id"):
        content_id = data.get("result", {}).get("content_id", "")
        logger.info(
            "Populated missing content ID for stream %s -> %s",
            infohash,
            content_id,
        )

    return content_id

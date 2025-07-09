"""Helper functions for AceStream scraper services."""

from acerestreamer.utils.logger import get_logger

from .models import FoundAceStream

logger = get_logger(__name__)


def create_unique_stream_list(streams: list[FoundAceStream]) -> dict[str, FoundAceStream]:
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

"""Helper functions for AceStream scraper services."""

from typing import TYPE_CHECKING

from acere.database.models.acestream import AceStreamDBEntry
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pydantic import HttpUrl

    from acere.services.scraper.models import FoundAceStream
else:
    HttpUrl = object
    FoundAceStream = object

logger = get_logger(__name__)


def create_extinf_line(
    stream: FoundAceStream | AceStreamDBEntry,
    tvg_url_base: HttpUrl | None,
    last_found: int,
) -> str:
    """Create an M3U EXTINF line for a given FoundAceStream object."""
    final_url_base = None
    if tvg_url_base is not None:
        final_url_base = tvg_url_base.encoded_string().removesuffix("/")
    out = [
        "#EXTINF:-1",
        f'tvg-logo="{final_url_base}/{stream.tvg_logo}"' if stream.tvg_logo and final_url_base else "",
        f'tvg-id="{stream.tvg_id}"',
        f'group-title="{stream.group_title}"',
        f'x-last-found="{last_found}"',
    ]

    return " ".join(part for part in out if part) + f", {stream.title}\n"

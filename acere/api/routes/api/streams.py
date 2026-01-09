"""Main Stream Site Blueprint."""

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import (
    get_current_user,
)
from acere.instances.scraper import get_ace_scraper
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from acere.services.ace_quality import Quality
    from acere.services.scraper.models import FoundAceStreamAPI
else:
    Quality = object
    FoundAceStreamAPI = object

logger = get_logger(__name__)

router = APIRouter(prefix="/streams", tags=["Streams"], dependencies=[Depends(get_current_user)])


# region /api/stream(s)
@router.get("/content_id/{content_id}")
def by_content_id(content_id: str) -> FoundAceStreamAPI:
    """API endpoint to get a specific stream by Ace ID."""
    ace_scraper = get_ace_scraper()
    found_stream = ace_scraper.get_stream_by_content_id_api(content_id)
    if not found_stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    return found_stream


@router.get("/")
def streams() -> list[FoundAceStreamAPI]:
    """API endpoint to get the flat streams."""
    ace_scraper = get_ace_scraper()
    return ace_scraper.get_stream_list_api()


@router.get("/health")
def health() -> dict[str, Quality]:
    """API endpoint to get the streams."""
    ace_scraper = get_ace_scraper()
    return ace_scraper.get_streams_health()

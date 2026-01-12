"""Blueprint for EPG API Endpoints."""


from fastapi import APIRouter, Depends

from acere.api.deps import get_current_user
from acere.instances.scraper import get_ace_scraper
from acere.services.epg.models import EPGApiHandlerResponse

router = APIRouter(
    prefix="/epg",
    tags=["EPG"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def epgs() -> EPGApiHandlerResponse:
    """Get the list of EPGs."""
    ace_scraper = get_ace_scraper()
    return ace_scraper.epg_handler.get_epgs_api()

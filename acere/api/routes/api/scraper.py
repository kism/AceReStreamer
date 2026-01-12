"""Scraper API Blueprint."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import (
    get_current_active_superuser,
    get_current_user,
)
from acere.core.config import ScrapeSiteAPI, ScrapeSiteHTML, ScrapeSiteIPTV
from acere.instances.config import settings
from acere.instances.scraper import get_ace_scraper
from acere.services.scraper.models import AceScraperSourceApi
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/scraper", tags=["Scraper"])


@router.get("/source", dependencies=[Depends(get_current_user)])
def sources() -> list[AceScraperSourceApi]:
    """API endpoint to get the flat streams sources."""
    ace_scraper = get_ace_scraper()
    return ace_scraper.get_scraper_sources_flat_api()


@router.get("/source/{source_slug}", dependencies=[Depends(get_current_user)])
def source(source_slug: str) -> AceScraperSourceApi:
    """API endpoint to get a single stream source by its slug."""
    ace_scraper = get_ace_scraper()
    wip = ace_scraper.get_scraper_sources_flat_api()
    for source in wip:
        if source.name == source_slug:
            return source

    raise HTTPException(status_code=HTTPStatus.NOT_FOUND)


@router.post("/source", dependencies=[Depends(get_current_active_superuser)])
def add_source(  # noqa: C901 Revisit once I have some tests
    body_json: AceScraperSourceApi | list[AceScraperSourceApi],
) -> MessageResponseModel:
    errors: list[str] = []
    if not body_json:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=MessageResponseModel(message="json is empty"),
        )

    if not isinstance(body_json, (list)):
        body_json = [body_json]

    for n, item in enumerate(body_json):
        item_msg = ""
        item_success = True

        if item.type == "iptv":
            iptv = ScrapeSiteIPTV(**item.model_dump())
            item_success, item_msg = settings.scraper.add_iptv_source(iptv)
        elif item.type == "api":
            api = ScrapeSiteAPI(**item.model_dump())
            item_success, item_msg = settings.scraper.add_api_source(api)
        elif item.type == "html":
            html = ScrapeSiteHTML(**item.model_dump())
            item_success, item_msg = settings.scraper.add_html_source(html)
        else:
            item_success = False
            item_msg = "Invalid source type"

        if not item_success:
            errors.append(f"Item {n}: {item_msg}")

    if errors:
        msg = "Errors adding sources"
        if len(errors) == 1:
            msg = "Error adding source"
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=MessageResponseModel(message=msg, errors=errors).model_dump_json(),
        )

    settings.write_config()

    msg = "Sources added successfully"
    if len(body_json) == 1:
        msg = "Source added successfully"

    get_ace_scraper().start_scrape_thread()

    return MessageResponseModel(message=msg)


@router.delete("/source/{slug}", dependencies=[Depends(get_current_active_superuser)])
def remove_source(slug: str) -> MessageResponseModel:
    """API endpoint to remove an IPTV source."""
    success, msg = settings.scraper.remove_source(slug)
    if not success:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=MessageResponseModel(message="Unable to delete", errors=[msg]).model_dump_json(),
        )

    settings.write_config()

    return MessageResponseModel(message=msg)


@router.post("/check", dependencies=[Depends(get_current_active_superuser)])
async def check() -> MessageResponseModel:
    """API endpoint to attempt to check all streams health."""
    ace_scraper = get_ace_scraper()
    started = await ace_scraper.check_missing_quality()

    logger.info("/api/sources/check Health check started: %s", started)

    if started:
        response = MessageResponseModel(message="Health check started")
    else:
        response = MessageResponseModel(message="Health check already running")

    return response

"""Scraper API Blueprint."""

from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from acere.core.config.scraper import ScrapeSiteAPI, ScrapeSiteHTML, ScrapeSiteIPTV
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.config import settings
from acere.instances.scraper import get_ace_scraper
from acere.services.scraper.models import AceScraperSourceApi
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/scraper", tags=["Scraper"])


@router.get("/source")
def sources() -> list[AceScraperSourceApi]:
    """API endpoint to get the flat streams sources."""
    ace_scraper = get_ace_scraper()
    return ace_scraper.get_scraper_sources_flat_api()


@router.get("/source/{source_slug}")
def source(source_slug: str) -> AceScraperSourceApi:
    """API endpoint to get a single stream source by its slug."""
    ace_scraper = get_ace_scraper()
    wip = ace_scraper.get_scraper_sources_flat_api()
    for source in wip:
        if source.name == source_slug:
            return source

    raise HTTPException(status_code=HTTPStatus.NOT_FOUND)


@router.post("/source")
def add_source(  # noqa: C901 Revisit once I have some tests
    body_json: AceScraperSourceApi | list[AceScraperSourceApi],
) -> MessageResponseModel:
    errors: list[str] = []
    if not body_json:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="json is empty",
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
            detail=msg,
        )

    msg = "Sources added successfully"
    if len(body_json) == 1:
        msg = "Source added successfully"

    settings.write_config()
    get_ace_scraper().start_scrape_thread()

    return MessageResponseModel(message=msg)


@router.put("/source/{slug}")
def update_source(slug: str, body_json: AceScraperSourceApi) -> MessageResponseModel:
    """API endpoint to update (replace) an existing scraper source."""
    new_site: ScrapeSiteHTML | ScrapeSiteIPTV | ScrapeSiteAPI
    if body_json.type == "iptv":
        new_site = ScrapeSiteIPTV(**body_json.model_dump())
    elif body_json.type == "api":
        new_site = ScrapeSiteAPI(**body_json.model_dump())
    else:
        new_site = ScrapeSiteHTML(**body_json.model_dump())

    success, msg = settings.scraper.update_source(slug, new_site)
    if not success:
        status = HTTPStatus.NOT_FOUND if "not found" in msg.lower() else HTTPStatus.BAD_REQUEST
        raise HTTPException(status_code=status, detail=msg)

    settings.write_config()
    get_ace_scraper().start_scrape_thread()

    return MessageResponseModel(message=msg)


@router.delete("/source/{slug}")
def remove_source(slug: str) -> MessageResponseModel:
    """API endpoint to remove a scraper source."""
    success, msg = settings.scraper.remove_source(slug)
    if not success:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=msg,
        )

    settings.write_config()
    # No need to rescrape since the database will have whatever this source found

    return MessageResponseModel(message=msg)


@router.get("/name-override")
def get_name_overrides() -> dict[str, str]:
    """API endpoint to get the scraper name overrides."""
    return settings.scraper.content_id_infohash_name_overrides


@router.delete("/name-override/{content_id}")
def delete_name_override(content_id: str) -> MessageResponseModel:
    """API endpoint to delete a scraper name override."""
    success = settings.scraper.delete_content_id_name_override(content_id)
    if not success:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Content ID name override not found",
        )

    settings.write_config()
    get_ace_scraper().start_scrape_thread()
    return MessageResponseModel(message="Content ID name override deleted successfully")


@router.post("/name-override/{content_id}")
def add_name_override(content_id: str, name: str) -> MessageResponseModel:
    """API endpoint to add a scraper name override, key can be a content_id or infohash."""
    settings.scraper.add_content_id_name_override(content_id, name)

    # Apply immediately to any existing stream, rather than waiting for the next scrape
    handler = get_ace_streams_db_handler()
    resolved_content_id = content_id
    if not handler.get_by_content_id(resolved_content_id):
        resolved_content_id = handler.get_content_id_from_infohash(content_id) or ""
    if resolved_content_id:
        handler.update_title(resolved_content_id, name)

    settings.write_config()
    get_ace_scraper().start_scrape_thread()
    return MessageResponseModel(message="Content ID name override added successfully")

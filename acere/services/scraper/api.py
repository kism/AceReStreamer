"""API Scraper."""

from typing import TYPE_CHECKING

import aiohttp
from pydantic import BaseModel, ConfigDict, ValidationError

from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.logger import get_logger

from .common import ScraperCommon
from .models import FoundAceStream

if TYPE_CHECKING:
    from acere.core.config import ScrapeSiteAPI, TitleFilter
else:
    ScrapeSiteAPI = object
    TitleFilter = object


logger = get_logger(__name__)


class APISiteResponseItem(BaseModel):
    """Model API response."""

    model_config = ConfigDict(extra="ignore")  # I dont trust extras

    infohash: str
    name: str
    availability: float
    availability_updated_at: int
    categories: list[str] | None = None


class APIStreamScraper(ScraperCommon):
    """API Scraper object."""

    async def scrape_api_endpoints(self, sites: list[ScrapeSiteAPI]) -> list[FoundAceStream]:
        """Scrape the streams from the configured API sites."""
        found_streams: list[FoundAceStream] = []

        for site in sites:
            streams = await self._scrape_api_endpoint(site)
            if streams:
                found_streams.extend(streams)

        return found_streams

    async def _scrape_api_endpoint(self, site: ScrapeSiteAPI) -> list[FoundAceStream]:
        """Scrape the streams from the configured API site."""
        streams: list[FoundAceStream] = []

        logger.debug("Scraping streams from API site: %s", site.name)
        try:
            async with aiohttp.ClientSession() as session:  # noqa: SIM117
                async with session.get(site.url.encoded_string()) as response:
                    response.raise_for_status()
                    response_json = await response.json()
        except aiohttp.ClientError as e:
            log_aiohttp_exception(logger, site.url, e)
            return []

        logger.debug("Scraped %d items from API site: %s", len(response_json), site.name)
        stream_list: list[APISiteResponseItem] = []
        for item in response_json:
            try:
                stream_list.append(APISiteResponseItem(**item))
            except ValidationError:
                logger.exception("Failed to validate API response item: %s", item)

        for stream in stream_list:
            title = self.name_processor.cleanup_candidate_title(stream.name)

            if not self.name_processor.check_title_allowed(title=title, title_filter=site.title_filter):
                continue

            tvg_id = self.name_processor.get_tvg_id_from_title(title)
            group_title = stream.categories[0] if stream.categories else ""
            group_title = self.name_processor.populate_group_title(group_title, title)
            tvg_logo = self.name_processor.find_tvg_logo_image(title)

            # We call it fresh if availability is 100%
            last_found_time = stream.availability_updated_at if stream.availability < 1 else 0

            streams.append(
                FoundAceStream(
                    title=title,
                    infohash=stream.infohash,
                    tvg_id=tvg_id,
                    group_title=group_title,
                    tvg_logo=tvg_logo,
                    site_names=[site.name],
                    last_found_time=last_found_time,
                )
            )

        return streams

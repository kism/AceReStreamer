"""Custom Pydantic models (objects) for scraping."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, Self

from pydantic import AnyUrl, BaseModel, HttpUrl, field_serializer, model_validator

from acere.core.config.scraper import HTMLScraperFilter, TitleFilter
from acere.utils.helpers import check_valid_content_id_or_infohash

if TYPE_CHECKING:
    from pathlib import Path

    from acere.core.config.scraper import ScrapeSiteHTML, ScrapeSiteIPTV

else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object
    Path = object


class ManuallyAddedAceStream(BaseModel):
    """Model for a manually added AceStream."""

    title: str
    content_id: str
    group_title: str


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    content_id: str = ""
    infohash: str | None = None
    tvg_id: str
    tvg_logo: str | None = None
    group_title: str = ""
    sites_found_on: list[str]
    last_scraped_time: datetime = datetime.now(tz=UTC)

    @model_validator(mode="after")
    def manual_validate(self) -> Self:
        """Validate the AceStream ID manually."""
        if not self.content_id and not self.infohash:
            msg = "FoundAceStream: Either content_id or infohash must be provided"
            raise ValueError(msg)

        if self.content_id and not check_valid_content_id_or_infohash(self.content_id):
            msg = f"FoundAceStream: Invalid AceStream content_id: {self.content_id}"
            raise ValueError(msg)

        if self.infohash and not check_valid_content_id_or_infohash(self.infohash):
            msg = f"FoundAceStream: Invalid AceStream infohash: {self.infohash}"
            raise ValueError(msg)

        if self.infohash == "":
            msg = "FoundAceStream: infohash cannot be an empty string"
            raise ValueError(msg)

        if not self.title:
            msg = "FoundAceStream: Title cannot be empty"
            raise ValueError(msg)

        return self


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    ace_uri: AnyUrl
    title_candidates: list[str] = []


class FoundAceStreamAPI(BaseModel):
    """Model for a found AceStream."""

    # KIERAN DO NOT MAKE THIS A DICT, ITS NOT WORTH IT

    title: str
    content_id: str
    infohash: str | None = None
    tvg_id: str
    tvg_logo: str | None = None
    last_scraped_time: datetime
    # EPG
    program_title: str  # Forces me to try populate it
    program_description: str  # Forces me to try populate it
    # Quality
    quality: int
    has_ever_worked: bool
    m3u_failures: int


class AceScraperSourcesApi(BaseModel):
    """Represent the sources of the AceScraper, for API use."""

    html: list[ScrapeSiteHTML]
    iptv_m3u8: list[ScrapeSiteIPTV]


class AceScraperSourceApi(BaseModel):
    """Represent a scraper instance, generic for HTML and IPTV sources."""

    name: str
    url: HttpUrl
    title_filter: TitleFilter = TitleFilter()
    html_filter: HTMLScraperFilter | None = None
    type: Literal["html", "iptv", "api"]

    @model_validator(mode="after")
    def validate_html_only_options(self) -> Self:
        """Validate options that are only applicable to HTML sources."""
        if self.type == "html":
            if not self.html_filter:
                self.html_filter = HTMLScraperFilter()

        elif self.type in {"iptv", "api"} and self.html_filter is not None:
            self.html_filter = None

        return self

    @field_serializer("url")
    def serialize_url(self, value: HttpUrl) -> str:
        """Serialize URL to string."""
        return value.encoded_string()

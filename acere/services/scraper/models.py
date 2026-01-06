"""Custom Pydantic models (objects) for scraping."""

from typing import TYPE_CHECKING, Literal, Self

from pydantic import AnyUrl, BaseModel, HttpUrl, field_serializer, model_validator

from acere.core.config import HTMLScraperFilter, TitleFilter
from acere.utils.helpers import check_valid_content_id_or_infohash

if TYPE_CHECKING:
    from acere.core.config import ScrapeSiteHTML, ScrapeSiteIPTV
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    content_id: str = ""
    infohash: str = ""
    tvg_id: str
    tvg_logo: str | None = None
    group_title: str = ""
    site_names: list[str]
    quality: int = -1
    last_found_time: int = 0  # = 0 # Epoch of last found time, 0 if fresh

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

        if not self.title:
            msg = "FoundAceStream: Title cannot be empty"
            raise ValueError(msg)

        return self


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    ace_uri: AnyUrl
    title_candidates: list[str] = []


class FoundAceStreamAPI(BaseModel):
    """Flat model for a found AceStream."""

    site_names: list[str]
    quality: int
    title: str
    content_id: str
    infohash: str
    tvg_id: str
    tvg_logo: str | None = None
    program_title: str = ""
    program_description: str = ""
    has_ever_worked: bool


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

        elif self.type in {"iptv", "api"}:
            if self.html_filter is not None:
                self.html_filter = None

        return self

    @field_serializer("url")
    def serialize_url(self, value: HttpUrl) -> str:
        """Serialize URL to string."""
        return value.encoded_string()

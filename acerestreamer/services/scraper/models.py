"""Custom Pydantic models (objects) for scraping."""

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, model_validator

from acerestreamer.config.models import TitleFilter
from acerestreamer.utils import check_valid_content_id_or_infohash

if TYPE_CHECKING:
    from acerestreamer.config.models import ScrapeSiteHTML, ScrapeSiteIPTV
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    content_id: str = ""
    infohash: str = ""
    tvg_id: str
    tvg_logo: str
    quality: int = -1

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


class FoundAceStreams(BaseModel):
    """Model for a list of found AceStreams."""

    site_name: str
    site_slug: str
    stream_list: list[FoundAceStream]


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    content_id: str
    title_candidates: list[str] = []


class FlatFoundAceStream(BaseModel):
    """Flat model for a found AceStream."""

    site_names: list[str]
    quality: int
    title: str
    content_id: str
    infohash: str
    tvg_id: str
    tvg_logo: str
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
    slug: str
    url: str
    title_filter: TitleFilter
    type: str
    check_sibling: bool | None = None
    target_class: str | None = None

    @model_validator(mode="after")
    def validate_html_only_options(self) -> Self:
        """Validate options that are only applicable to HTML sources."""
        if self.type == "html":
            msg = "HTML source must have target_class and check_sibling defined"
            if not self.target_class:
                raise ValueError(msg)
            if self.check_sibling is None:
                raise ValueError(msg)
        elif self.type == "iptv":
            msg = "IPTV source must not have target_class or check_sibling defined"
            if self.target_class or self.check_sibling is not None:
                raise ValueError(msg)

        return self

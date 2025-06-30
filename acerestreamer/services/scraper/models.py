"""Custom Pydantic models (objects) for scraping."""

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, model_validator

from acerestreamer.utils import check_valid_ace_id

if TYPE_CHECKING:
    from acerestreamer.config.models import ScrapeSiteHTML, ScrapeSiteIPTV
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    ace_id: str
    tvg_id: str
    tvg_logo: str
    quality: int = -1

    @model_validator(mode="after")
    def manual_validate(self) -> Self:
        """Validate the AceStream ID manually."""
        if not check_valid_ace_id(self.ace_id):
            msg = f"FoundAceStream: Invalid AceStream ID: {self.ace_id}"
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

    ace_id: str
    title_candidates: list[str] = []


class FlatFoundAceStream(BaseModel):
    """Flat model for a found AceStream."""

    site_name: str
    quality: int
    title: str
    ace_id: str
    tvg_id: str
    tvg_logo: str
    has_ever_worked: bool


class AceScraperSourcesApi(BaseModel):
    """Represent the sources of the AceScraper, for API use."""

    html: list[ScrapeSiteHTML]
    iptv_m3u8: list[ScrapeSiteIPTV]


class AceScraperSourceApi(BaseModel):
    """Represent a scraper instance, generic for HTML and IPTV sources."""

    name: str
    slug: str
    epg: list[str] = []

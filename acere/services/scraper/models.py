"""Generic Pydantic models for scraping (shared between ace and iptv)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl, field_serializer

from acere.config.ace.scraper import TitleFilter
from acere.config.iptv import IPTVSourceM3U8, IPTVSourceXtream


class FoundIPTVStream(BaseModel):
    """Model for a found IPTV stream (non-ace, direct HTTP/HLS)."""

    title: str
    original_title: str = ""
    upstream_url: str
    source_name: str
    tvg_id: str = ""
    tvg_logo: str | None = None
    group_title: str = ""
    last_scraped_time: datetime


class FoundIPTVStreamAPI(BaseModel):
    """Model for an IPTV proxy stream, for API use."""

    title: str
    original_title: str
    slug: str
    upstream_url: str
    source_name: str
    tvg_id: str
    tvg_logo: str | None = None
    group_title: str
    last_scraped_time: datetime
    program_title: str
    program_description: str
    quality: int
    has_ever_worked: bool
    m3u_failures: int


class IPTVSourceApi(BaseModel):
    """Represent an IPTV proxy source, generic for Xtream and M3U8 sources."""

    name: str
    url: HttpUrl
    type: Literal["xtream", "m3u8"]
    title_filter: TitleFilter = TitleFilter()
    category_filter: TitleFilter = TitleFilter()
    max_active_streams: int = 0
    username: str | None = None
    password: str | None = None

    @field_serializer("url", mode="plain")
    def serialize_url(self, value: HttpUrl) -> str:
        """Serialize URL to string."""
        return value.encoded_string()

    @staticmethod
    def from_xtream(source: IPTVSourceXtream) -> IPTVSourceApi:
        """Create from an Xtream source config."""
        return IPTVSourceApi(
            name=source.name,
            url=source.url,
            type="xtream",
            title_filter=source.title_filter,
            category_filter=source.category_filter,
            max_active_streams=source.max_active_streams,
            username=source.username,
            password=source.password,
        )

    @staticmethod
    def from_m3u8(source: IPTVSourceM3U8) -> IPTVSourceApi:
        """Create from an M3U8 source config."""
        return IPTVSourceApi(
            name=source.name,
            url=source.url,
            type="m3u8",
            title_filter=source.title_filter,
            category_filter=source.category_filter,
            max_active_streams=source.max_active_streams,
        )


class CombinedStreamAPI(BaseModel):
    """Unified stream model combining ace and IPTV streams, for API use."""

    stream_type: Literal["ace", "iptv"]
    title: str
    stream_url: str
    tvg_id: str
    tvg_logo: str | None = None
    group_title: str
    last_scraped_time: datetime
    program_title: str
    program_description: str
    quality: int

"""IPTV proxy source configuration."""

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator

from acere.config.ace.scraper import TitleFilter
from acere.utils.helpers import slugify


class IPTVSourceXtream(BaseModel):
    """Config for an Xtream Codes IPTV source."""

    model_config = ConfigDict(extra="ignore")

    name: str
    url: HttpUrl
    username: str
    password: str
    title_filter: TitleFilter = TitleFilter()
    category_filter: TitleFilter = TitleFilter()
    category_rename: dict[str, str] = {}
    max_active_streams: int = 0  # 0 = unlimited

    @field_validator("name", mode="before")
    @classmethod
    def set_name(cls, value: str) -> str:
        """Set the name to a slugified version."""
        return slugify(value)


class IPTVSourceM3U8(BaseModel):
    """Config for an M3U8 URL IPTV source."""

    model_config = ConfigDict(extra="ignore")

    name: str
    url: HttpUrl
    title_filter: TitleFilter = TitleFilter()
    category_filter: TitleFilter = TitleFilter()
    category_rename: dict[str, str] = {}  # Optional mapping of original channel names to new names
    max_active_streams: int = 0  # 0 = unlimited

    @field_validator("name", mode="before")
    @classmethod
    def set_name(cls, value: str) -> str:
        """Set the name to a slugified version."""
        return slugify(value)


class IPTVProxyConf(BaseModel):
    """Top-level IPTV proxy configuration."""

    model_config = ConfigDict(extra="ignore")

    xtream: list[IPTVSourceXtream] = []
    m3u8: list[IPTVSourceM3U8] = []

    @field_validator("xtream", "m3u8", mode="after")
    @classmethod
    def unique_source_names(
        cls, value: list[IPTVSourceXtream] | list[IPTVSourceM3U8]
    ) -> list[IPTVSourceXtream] | list[IPTVSourceM3U8]:
        """Ensure all source names are unique within each list."""
        names = [source.name for source in value]
        if len(names) != len(set(names)):
            msg = f"Duplicate IPTV source names found: {[n for n in names if names.count(n) > 1]}"
            raise ValueError(msg)
        return value

    def add_xtream_source(self, source: IPTVSourceXtream) -> tuple[bool, str]:
        """Add an Xtream Codes source."""
        if any(s.name == source.name for s in self.xtream):
            return False, f"Source with name '{source.name}' already exists"
        self.xtream.append(source)
        return True, "Source added"

    def add_m3u8_source(self, source: IPTVSourceM3U8) -> tuple[bool, str]:
        """Add an M3U8 source."""
        if any(s.name == source.name for s in self.m3u8):
            return False, f"Source with name '{source.name}' already exists"
        self.m3u8.append(source)
        return True, "Source added"

    def remove_source(self, name: str) -> tuple[bool, str]:
        """Remove a source by name from either list."""
        for xtream_source in self.xtream:
            if xtream_source.name == name:
                self.xtream.remove(xtream_source)
                return True, "Source removed"
        for m3u8_source in self.m3u8:
            if m3u8_source.name == name:
                self.m3u8.remove(m3u8_source)
                return True, "Source removed"
        return False, f"Source not found: {name}"

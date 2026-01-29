import urllib
import urllib.parse
from typing import TYPE_CHECKING, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    ValidationError,
    field_validator,
    model_validator,
)

from acere.utils.helpers import slugify
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object
logger = get_logger(__name__)


# region Models
class TitleFilter(BaseModel):
    """Model for title filtering.

    Items in regex_postprocessing will be applied to remove parts of the title via re.sub.

    The other lists will be evaluated in order:
    - always_exclude_words
    - always_include_words
    - exclude_words
    - include_words (if populated, otherwise allow any)
    """

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    always_exclude_words: list[str] = []
    always_include_words: list[str] = []
    exclude_words: list[str] = []
    include_words: list[str] = []
    regex_postprocessing: list[str] = []

    @field_validator("regex_postprocessing", mode="before")
    def ensure_list(cls, value: str | list[str]) -> list[str]:
        """Ensure the regex_postprocessing is a list."""
        if isinstance(value, str):
            value = [value]

        # Make unique, remove empty strings
        value = list(set(value))
        if "" in value:
            value.remove("")

        return value


class ScrapeSiteGeneric(BaseModel):
    """Generic Model for a site to scrape m3u8 or api streams."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    type: Literal["html", "iptv", "api"]
    name: str
    url: HttpUrl
    title_filter: TitleFilter = TitleFilter()

    @field_validator("name", mode="before")
    def set_name(cls, value: str) -> str:
        """Set the name to a slugified version."""
        return slugify(value)

    @model_validator(mode="after")
    def generate_slug(self) -> Self:
        """Generate a slug from the name."""
        if self.name == "":
            name_temp: str = slugify(urllib.parse.unquote(self.url.encoded_string()))

            self.name = name_temp

        return self


class HTMLScraperFilter(BaseModel):
    """Model for HTML scraper filtering."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    target_class: str = ""  # Target html class
    check_sibling: bool = False


class ScrapeSiteHTML(ScrapeSiteGeneric):
    """Model for a site to scrape."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    type: Literal["html"] = "html"
    html_filter: HTMLScraperFilter = HTMLScraperFilter()


class ScrapeSiteAPI(ScrapeSiteGeneric):
    """Scraper for API Sites."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    type: Literal["api"] = "api"

    @field_validator("url", mode="before")
    @classmethod
    def ensure_api_url_endswith(cls, value: str) -> str:
        """Ensure the API URL ends with a slash."""
        return value.removesuffix("/")


class ScrapeSiteIPTV(ScrapeSiteGeneric):
    """Scraper for IPTV Sites."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    type: Literal["iptv"] = "iptv"


# region AceScrapeConf
class AceScrapeConf(BaseModel):
    """Settings for scraping AceStreams."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    playlist_name: str = "acerestreamer"
    adhoc_playlist_external_url: HttpUrl | None = None
    tvg_logo_external_url: HttpUrl | None = None
    html: list[ScrapeSiteHTML] = []
    iptv_m3u8: list[ScrapeSiteIPTV] = []
    api: list[ScrapeSiteAPI] = []
    content_id_infohash_name_overrides: dict[str, str] = {}
    category_mapping: dict[str, list[str]] = {
        "sports": [
            "football",
            "soccer",
            "basketball",
            "nba",
            "sport",
            "tennis",
            "moto",
            "f1",
            "hockey",
            "cricket",
            "rugby",
            "golf",
        ],
        "movies": [
            "movie",
            "cinema",
            "film",
        ],
        "news": [
            "news",
        ],
        "kids": [
            "kids",
            "children",
        ],
        "music": [
            "music",
            "concert",
            "radio",
        ],
    }

    @field_validator("adhoc_playlist_external_url", mode="before")
    @classmethod
    def ensure_adhoc_playlist_url_endswith(cls, value: str | None) -> str | None:
        """Ensure the Adhoc playlist URL ends with a slash."""
        if value is None:
            return value
        return value.removesuffix("/")

    @field_validator("tvg_logo_external_url", mode="before")
    @classmethod
    def ensure_tvg_logo_url_endswith(cls, value: str | None) -> str | None:
        """Ensure the TVG logo URL ends with a slash."""
        if value is None:
            return value
        return value.removesuffix("/")

    @model_validator(mode="after")
    def unique_scraper_site_names(self) -> Self:
        """Ensure all scraper sites have unique names, via slug."""
        names_slug = []
        found_duplicate = []
        for site in self.html + self.iptv_m3u8:
            if site.name in names_slug:
                msg = f"  '{site.name}'"
                found_duplicate.append(msg)
            names_slug.append(site.name)

        if found_duplicate:
            msg = "Config: Duplicate scraper site names found, please ensure each site has a unique name.\n"
            msg += "Found duplicates:\n"
            msg += "\n".join(found_duplicate)
            msg += "\nComplete list of sites:\n"
            for site in self.html + self.iptv_m3u8:
                msg += f"  '{site.name}' -> '{site.name}'\n"

            raise ValueError(msg)

        return self

    @field_validator("playlist_name", mode="after")
    @classmethod
    def _slugify(cls, value: str) -> str:
        return slugify(value)

    def _print_results(self, source_type: str) -> None:
        total_scraper_count = len(self.html) + len(self.iptv_m3u8) + len(self.api)
        logger.info("Added new %s source, total sources: %d", source_type, total_scraper_count)

    def add_iptv_source(self, new_site: ScrapeSiteIPTV) -> tuple[bool, str]:
        """Add an IPTV source, no options."""
        logger.info("Adding new IPTV source")
        new_iptv = [*self.iptv_m3u8, new_site]

        try:
            validated = self.model_validate(
                {
                    "html": self.html,
                    "iptv_m3u8": new_iptv,
                    "api": self.api,
                }
            )
        except ValueError as e:
            return False, str(e)

        self.iptv_m3u8 = validated.iptv_m3u8
        self._print_results("iptv")

        return True, "Source added"

    def add_html_source(self, new_site: ScrapeSiteHTML) -> tuple[bool, str]:
        """Add an HTML source, no options."""
        logger.info("Adding new HTML source")
        new_html = [*self.html, new_site]

        try:
            validated = self.model_validate(
                {
                    "html": new_html,
                    "iptv_m3u8": self.iptv_m3u8,
                    "api": self.api,
                }
            )
        except ValueError as e:
            return False, str(e)

        self.html = validated.html
        self._print_results("html")

        return True, "Source added"

    def add_api_source(self, new_site: ScrapeSiteAPI) -> tuple[bool, str]:
        """Add an API source, no options."""
        logger.info("Adding new API source")
        new_api = [*self.api, new_site]

        try:
            validated = self.model_validate(
                {
                    "html": self.html,
                    "iptv_m3u8": self.iptv_m3u8,
                    "api": new_api,
                }
            )
        except ValueError as e:
            return False, str(e)

        self.api = validated.api
        self._print_results("iptv")

        return True, "Source added"

    def remove_source(self, site_name: str) -> tuple[bool, str]:  # noqa: C901 Revisit once I have some tests
        """Remove a source via slug."""
        logger.info("Removing source '%s'", site_name)

        in_iptv: bool = any(site.name == site_name for site in self.iptv_m3u8)
        in_html: bool = any(site.name == site_name for site in self.html)
        in_api: bool = any(site.name == site_name for site in self.api)

        if not in_iptv and not in_html and not in_api:
            return False, f"Source not found: {site_name}"

        sites: list[ScrapeSiteHTML] | list[ScrapeSiteAPI] | list[ScrapeSiteIPTV] = []

        if in_iptv:
            model_to_validate = "iptv_m3u8"
            sites = self.iptv_m3u8
        elif in_html:
            model_to_validate = "html"
            sites = self.html
        elif in_api:
            model_to_validate = "api"
            sites = self.api
        else:  # Shouldn't get here
            return False, f"Source not found: {site_name}"

        for site in sites:
            logger.warning(site.name)

        without_source_to_remove = [site for site in sites if site.name != site_name]

        for site in without_source_to_remove:
            logger.warning(site.name)

        try:
            validated = self.model_validate({model_to_validate: without_source_to_remove})
        except ValidationError as e:
            return False, str(e)

        if in_iptv:
            self.iptv_m3u8 = validated.iptv_m3u8
        elif in_html:
            self.html = validated.html
        elif in_api:
            self.api = validated.api

        logger.info("Scraper source removed, new count %s", len(self.iptv_m3u8))

        return True, "Source removed"

    def delete_content_id_name_override(self, content_id: str) -> bool:
        """Delete a content ID to name override."""
        if content_id in self.content_id_infohash_name_overrides:
            del self.content_id_infohash_name_overrides[content_id]
            logger.info("Deleted content ID name override for %s", content_id)
            return True

        return False

    def add_content_id_name_override(self, content_id: str, name: str) -> None:
        """Add a content ID to name override."""
        self.content_id_infohash_name_overrides[content_id] = name
        logger.info("Added content ID name override for %s", content_id)

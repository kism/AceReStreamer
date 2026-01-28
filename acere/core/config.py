import datetime
import json
import os
import secrets
import typing
import urllib
import urllib.parse
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    HttpUrl,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from acere.constants import ENV_PREFIX, OUR_TIMEZONE, SETTINGS_FILE
from acere.utils.helpers import slugify
from acere.utils.logger import LoggingConf, get_logger

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


def parse_cors(v: Any) -> list[str] | str:  # noqa: ANN401 JSON things
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    if isinstance(v, list | str):
        return v
    raise ValueError(v)


"""Config loading, setup, validating, writing."""


# Logging should be all done at INFO level or higher as the log level hasn't been set yet
# Modules should all setup logging like this so the log messages include the modules name.
logger = get_logger(__name__)


# region Scraper Models
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

    playlist_name: str = "AceReStreamer"
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


# region AppConf
class AppConf(BaseModel):
    """Application configuration definition."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    authentication_enabled: bool = True
    ace_address: HttpUrl = HttpUrl("http://localhost:6878")
    transcode_audio: bool = True
    ace_max_streams: int = 4

    @field_validator("ace_max_streams", mode="after")
    @classmethod
    def validate_max_streams(cls, value: int) -> int:
        """Validate the max streams."""
        n_min_streams = 1
        n_default_streams = 4
        n_high_streams = 10
        n_very_high_streams = 20

        if value < n_min_streams:
            msg = (
                f"ace_max_streams '{value}' must be at least {n_min_streams}, setting to default of {n_default_streams}"
            )
            logger.warning(msg)
            value = n_default_streams

        if value > n_high_streams and value <= n_very_high_streams:
            logger.warning(
                "You have set ace_max_streams to a high value (%d), this may cause performance issues.",
                value,
            )
        elif value > n_very_high_streams:
            logger.warning(
                "You have set ace_max_streams to a VERY high value (%d), this will likely cause performance issues.",
                value,
            )

        return value


# region EPGInstanceConf
class EPGInstanceConf(BaseModel):
    """EPG (Electronic Program Guide) configuration definition.

    tvg_id_overrides is a str:str dict where you can override stream tvg_ids to match those in the EPG.
    """

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    format: Literal["xml.gz", "xml"] = "xml.gz"
    url: HttpUrl
    tvg_id_overrides: dict[
        str, str
    ] = {}  # The program normanises the tvg_ids pretty well, but sometimes you need to override specific ones.

    @computed_field
    @property
    def slug(self) -> str:
        """Generate a slug from the url."""
        return slugify(urllib.parse.unquote(self.url.encoded_string()))


# region AceReStreamerConf
class AceReStreamerConf(BaseSettings):
    """Settings Definition."""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env" if not os.getenv("ACERE_TESTING") else None,
        env_prefix=ENV_PREFIX,
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        json_file=SETTINGS_FILE,
    )

    # Default values for our settings
    app: AppConf = AppConf()
    logging: LoggingConf = LoggingConf()
    scraper: AceScrapeConf = AceScrapeConf()
    epgs: list[EPGInstanceConf] = []
    FRONTEND_HOST: str = ""  # Set to http://localhost:5173 for local dev
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    EXTERNAL_URL: str = "http://localhost:5100"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SECRET_KEY: str = ""
    FIRST_SUPERUSER: str = "admin"
    FIRST_SUPERUSER_PASSWORD: str = ""
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003 Don't use buy must include.
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Specify the priority of settings sources."""
        # Skip dotenv loading when in test mode
        if os.getenv("ACERE_TESTING"):
            return (
                init_settings,
                env_settings,
                JsonConfigSettingsSource(settings_cls),
            )
        return (  # pragma: no cover
            init_settings,
            dotenv_settings,
            env_settings,
            JsonConfigSettingsSource(settings_cls),
        )

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """Validate the secret key, generate one if not set."""
        if not value or value.strip() == "":
            value = secrets.token_urlsafe(32)
        return value

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [self.FRONTEND_HOST]

    def add_epg(self, epg: EPGInstanceConf) -> None:
        """Add an EPG instance to the config."""
        matching_epg = next((existing_epg for existing_epg in self.epgs if existing_epg.url == epg.url), None)

        if not matching_epg:
            self.epgs.append(epg)
            logger.info("Added new EPG source, total sources: %d", len(self.epgs))
        else:
            matching_epg = epg
            logger.info("Updating existing EPG source: %s", epg.url)

    def remove_epg(self, epg_url_slug: str) -> bool:
        """Remove an EPG instance from the config via URL."""
        matching_epg = next((existing_epg for existing_epg in self.epgs if existing_epg.slug == epg_url_slug), None)

        if matching_epg:
            self.epgs.remove(matching_epg)
            logger.info("Removed EPG source, total sources: %d", len(self.epgs))
            return True

        return False

    def write_backup_config(
        self,
        config_path: Path | None,
        existing_data: typing.Any,  # noqa: ANN401
        reason: str = "Validation has changed the config file",
    ) -> None:
        if config_path is None:
            config_path = SETTINGS_FILE

        time_str = datetime.datetime.now(tz=OUR_TIMEZONE).strftime("%Y-%m-%d_%H%M%S")
        config_backup_dir = config_path.parent / "config_backups"
        config_backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = config_backup_dir / f"{config_path.stem}_{time_str}{config_path.suffix}.bak"
        logger.warning(
            "%s, backing up the old one to %s",
            reason,
            backup_file,
        )
        with backup_file.open("w") as f:
            f.write(json.dumps(existing_data))

    def write_config(self, config_path: Path | None = None) -> None:
        """Write the current settings to a JSON file."""
        if config_path is None:
            config_path = SETTINGS_FILE

        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = json.loads(self.model_dump_json())

        if not config_path.exists():
            logger.warning("Writing fresh config file at %s", config_path.absolute())
            config_path.touch()
            existing_data = config_data
        else:
            with config_path.open("r") as f:
                existing_data = json.load(f)

        if existing_data != config_data:  # The new object will be valid, so we back up the old one
            self.write_backup_config(config_path, existing_data)

        with config_path.open("w") as f:
            f.write(json.dumps(config_data))

        config_path_json = config_path.with_suffix(".json")
        logger.info("Writing config to %s", config_path_json)
        with config_path_json.open("w") as f:
            f.write(self.model_dump_json(indent=2, exclude_none=False))

        logger.info("Config write complete")

    @classmethod
    def force_load_config_file(cls, config_path: Path) -> Self:
        """Load the configuration file. File contents takes precedence over env vars."""
        if not config_path.exists() or not config_path.is_file():
            logger.warning(
                "Config file %s does not exist, loading defaults",
                config_path.absolute(),
            )
            return cls()

        logger.info("Loading config from %s", config_path.absolute())
        with config_path.open("r") as f:
            config = json.load(f)

        return cls(**config)

    @classmethod
    def force_load_defaults(cls) -> Self:
        """Load the default configuration, ignoring config file and env vars."""
        logger.info("Loading default config")
        return cls()

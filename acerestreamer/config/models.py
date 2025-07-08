"""Config loading, setup, validating, writing."""

import datetime
import json
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from acerestreamer.utils import slugify
from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import LoggingConf, get_logger

# Logging should be all done at INFO level or higher as the log level hasn't been set yet
# Modules should all setup logging like this so the log messages include the modules name.
logger = get_logger(__name__)


class FlaskConf(BaseModel):
    """Flask configuration definition."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    DEBUG: bool = False
    TESTING: bool = False
    SERVER_NAME: str = "http://127.0.0.1:5100"


class TitleFilter(BaseModel):
    """Model for title filtering."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    always_exclude_words: list[str] = []
    always_include_words: list[str] = []
    exclude_words: list[str] = []
    include_words: list[str] = []
    regex_postprocessing: str = ""


class ScrapeSiteHTML(BaseModel):
    """Model for a site to scrape."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    name: str = "Example HTML"
    slug: str = ""
    url: str = "https://example.com"
    target_class: str = ""  # Target html class
    check_sibling: bool = False
    title_filter: TitleFilter = TitleFilter()

    @model_validator(mode="after")
    def valid_url(self) -> Self:
        """Validate the URL."""
        self.url = self.url.strip()
        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            msg = f"Error loading config: URL for {self.name} must start with 'http://' or 'https://'"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def generate_slug(self) -> Self:
        """Generate a slug from the name."""
        name_slug = slugify(self.name)

        if self.slug == "":
            self.slug = name_slug
        elif self.slug != name_slug:
            logger.warning("You cannot manually set the slug. It will be generated from the name.")

        self.slug = slugify(self.name)

        return self


class ScrapeSiteIPTV(BaseModel):
    """Model for a site to scrape IPTV streams."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    name: str = "Example IPTV"
    slug: str = ""
    url: str = "https://example.com/iptv.txt"
    title_filter: TitleFilter = TitleFilter()

    @model_validator(mode="after")
    def valid_url(self) -> Self:
        """Validate the URL."""
        self.url = self.url.strip()
        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            msg = f"Error loading config: URL for {self.name} must start with 'http://' or 'https://'"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def generate_slug(self) -> Self:
        """Generate a slug from the name."""
        name_slug = slugify(self.name)

        if self.slug == "":
            self.slug = name_slug
        elif self.slug != name_slug:
            logger.warning("You cannot manually set the slug. It will be generated from the name.")

        self.slug = slugify(self.name)

        return self


class AceScrapeConf(BaseModel):
    """Settings for scraping AceStreams."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    html: list[ScrapeSiteHTML] = []
    iptv_m3u8: list[ScrapeSiteIPTV] = []

    @model_validator(mode="after")
    def unique_scraper_site_names(self) -> Self:
        """Ensure all scraper sites have unique names, via slug."""
        names_slug = []
        found_duplicate = []
        for site in self.html + self.iptv_m3u8:
            if site.slug in names_slug:
                msg = f"  '{site.name}' -> '{site.slug}'"
                found_duplicate.append(msg)
            names_slug.append(site.slug)

        if found_duplicate:
            msg = "Config: Duplicate scraper site names found, please ensure each site has a unique name.\n"
            msg += "Found duplicates:\n"
            msg += "\n".join(found_duplicate)
            msg += "\nComplete list of sites:\n"
            for site in self.html + self.iptv_m3u8:
                msg += f"  '{site.name}' -> '{site.slug}'\n"

            raise ValueError(msg)

        return self


class AppConf(BaseModel):
    """Application configuration definition."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    password: str = ""
    ace_address: str = "http://localhost:6878"
    transcode_audio: bool = True
    ace_max_streams: int = 4

    @model_validator(mode="after")
    def valid_ace_address(self) -> Self:
        """Validate the configuration."""
        ace_address_temp = self.ace_address.strip().rstrip("/")
        if not ace_address_temp.startswith("http://"):
            msg = f"ace_address '{ace_address_temp}' must start with 'http://'"
            raise ValueError(msg)
        self.ace_address = ace_address_temp
        return self

    @model_validator(mode="after")
    def validate_max_streams(self) -> Self:
        """Validate the max streams."""
        n_min_streams = 1
        n_high_streams = 10
        n_very_high_streams = 20

        if self.ace_max_streams < n_min_streams:
            msg = f"ace_max_streams '{self.ace_max_streams}' must be at least {n_min_streams}"
            raise ValueError(msg)

        if self.ace_max_streams > n_high_streams:
            logger.warning(
                "You have set ace_max_streams to a high value (%d), this may cause performance issues.",
                self.ace_max_streams,
            )
        elif self.ace_max_streams > n_very_high_streams:
            logger.warning(
                "You have set ace_max_streams to a VERY high value (%d), this will likely cause performance issues.",
                self.ace_max_streams,
            )
        return self


class EPGInstanceConf(BaseModel):
    """EPG (Electronic Program Guide) configuration definition."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    region_code: str = "UK"
    format: str = "xml.gz"
    url: str = "https://www.open-epg.com/files/unitedkingdom1.xml.gz"


class AceReStreamerConf(BaseSettings):
    """Settings loaded from a TOML file."""

    model_config = SettingsConfigDict(extra="ignore")

    # Default values for our settings
    app: AppConf = AppConf()
    flask: FlaskConf = FlaskConf()
    logging: LoggingConf = LoggingConf()
    scraper: AceScrapeConf = AceScrapeConf()
    epgs: list[EPGInstanceConf] = []

    def write_config(self, config_location: Path) -> None:
        """Write the current settings to a TOML file."""
        config_location.parent.mkdir(parents=True, exist_ok=True)

        config_data = json.loads(self.model_dump_json())

        if not config_location.exists():
            logger.warning("Config file does not exist, creating it at %s", config_location)
            config_location.touch()
            existing_data = config_data
        else:
            with config_location.open("r") as f:
                existing_data = json.load(f)

        logger.info("Writing config to %s", config_location)

        new_file_content_str = json.dumps(config_data)

        if existing_data != config_data:  # The new object will be valid, so we back up the old one
            time_str = datetime.datetime.now(tz=OUR_TIMEZONE).strftime("%Y-%m-%d_%H%M%S")
            config_backup_dir = config_location.parent / "config_backups"
            config_backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = config_backup_dir / f"{config_location.stem}_{time_str}{config_location.suffix}.bak"
            logger.warning("Validation has changed the config file, backing up the old one to %s", backup_file)
            with backup_file.open("w") as f:
                f.write(json.dumps(existing_data))

        with config_location.open("w") as f:
            f.write(new_file_content_str)

        config_location_json = config_location.with_suffix(".json")
        logger.info("Writing config to %s", config_location_json)
        with config_location_json.open("w") as f:
            f.write(self.model_dump_json(indent=2, exclude_none=False))

    @classmethod
    def load_config(cls, config_path: Path) -> Self:
        """Load the configuration file."""
        if not config_path.exists():
            return cls()

        with config_path.open("r") as f:
            config = json.load(f)

        return cls(**config)

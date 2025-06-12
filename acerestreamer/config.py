"""Config loading, setup, validating, writing."""

import datetime
import json
from pathlib import Path
from typing import Self

import tomlkit
from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings

from .logger import get_logger

# Logging should be all done at INFO level or higher as the log level hasn't been set yet
# Modules should all setup logging like this so the log messages include the modules name.
logger = get_logger(__name__)


class FlaskConfDef(BaseModel):
    """Flask configuration definition."""

    DEBUG: bool = False
    TESTING: bool = False
    SERVER_NAME: str = "http://127.0.0.1:5100"


class TitleFilter(BaseModel):
    """Model for title filtering."""

    always_exclude_words: list[str] = []
    always_include_words: list[str] = []
    exclude_words: list[str] = []
    include_words: list[str] = []
    regex_postprocessing: str = ""


class ScrapeSiteHTML(BaseModel):
    """Model for a site to scrape."""

    name: str = "Example"
    url: str = "https://example.com"
    target_class: str = ""  # Target html class
    check_sibling: bool = False
    title_filter: TitleFilter = TitleFilter()

    @model_validator(mode="after")
    def valid_url(self) -> Self:
        """Validate the URL."""
        self.url = self.url.strip()
        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            msg = f"URL for {self.name} must start with 'http://' or 'https://'"
            raise ValueError(msg)
        return self


class ScrapeSiteIPTV(BaseModel):
    """Model for a site to scrape IPTV streams."""

    name: str = "Example IPTV"
    url: str = "https://example.com/iptv.txt"
    title_filter: TitleFilter = TitleFilter()


class AceScrapeSettings(BaseModel):
    """Settings for scraping AceStreams."""

    html: list[ScrapeSiteHTML] = []
    iptv_m3u8: list[ScrapeSiteIPTV] = []
    scrape_interval: int = 7200  # 2 hours


class AppConfDef(BaseModel):
    """Application configuration definition."""

    password: str = ""
    ace_address: str = "http://localhost:6878"

    @model_validator(mode="after")
    def valid_ace_address(self) -> Self:
        """Validate the configuration."""
        self.ace_address = self.ace_address.strip()
        self.ace_address = self.ace_address.rstrip("/")  # Remove trailing slash if it exists
        if self.ace_address.startswith("http://") or self.ace_address.startswith("https://"):
            return self
        msg = "ace_address must start with 'http://'"
        raise ValueError(msg)


class LoggingConfDef(BaseModel):
    """Logging configuration definition."""

    level: str = "INFO"
    path: Path | str = ""


class NginxConfDef(BaseModel):
    """Nginx configuration definition."""

    # CLI config generation only
    server_name: str = ""
    dhparam_path: Path | str = ""
    cert_path: Path | str = ""
    cert_key_path: Path | str = ""
    extra_config_file_path: Path | str = ""  # Example /etc/letsencrypt/options-ssl-nginx.conf

    # Actually used in the webapp, used to generate the ip allow list for nginx
    ip_allow_list_path: Path | str = ""


class AcestreamWebplayerConfig(BaseSettings):
    """Settings loaded from a TOML file."""

    # Default values for our settings
    app: AppConfDef = AppConfDef()
    flask: FlaskConfDef = FlaskConfDef()
    nginx: NginxConfDef | None = None  # Nginx configuration is optional
    logging: LoggingConfDef = LoggingConfDef()
    scraper: AceScrapeSettings = AceScrapeSettings()

    def write_config(self, config_location: Path) -> None:
        """Write the current settings to a TOML file."""
        from . import PROGRAM_NAME, URL, __version__

        config_location.parent.mkdir(parents=True, exist_ok=True)

        config_data = json.loads(self.model_dump_json())  # This is how we make the object safe for tomlkit
        if self.nginx is None:
            config_data.pop("nginx")  # Remove nginx if it is None

        if not config_location.exists():
            logger.warning("Config file does not exist, creating it at %s", config_location)
            config_location.touch()
            existing_data = config_data
        else:
            with config_location.open("r") as f:
                existing_data = tomlkit.load(f)

        logger.info("Writing config to %s", config_location)

        new_file_content_str = f"# Configuration file for {PROGRAM_NAME} v{__version__} {URL}\n"
        new_file_content_str += tomlkit.dumps(config_data)

        if existing_data != config_data:  # The new object will be valid, so we back up the old one
            local_tz = datetime.datetime.now().astimezone().tzinfo
            time_str = datetime.datetime.now(tz=local_tz).strftime("%Y-%m-%d_%H%M%S")
            backup_file = config_location.parent / f"{config_location.stem}_{time_str}{config_location.suffix}.bak"
            logger.warning("Validation has changed the config file, backing up the old one to %s", backup_file)
            with backup_file.open("w") as f:
                f.write(tomlkit.dumps(existing_data))

        with config_location.open("w") as f:
            f.write(new_file_content_str)


def load_config(config_path: Path) -> AcestreamWebplayerConfig:
    """Load the configuration file."""
    import tomlkit

    if not config_path.exists():
        return AcestreamWebplayerConfig()

    with config_path.open("r") as f:
        config = tomlkit.load(f)

    return AcestreamWebplayerConfig(**config)

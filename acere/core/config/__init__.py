"""Config loading, setup, validating, writing."""

import json
import os
import secrets
import typing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    HttpUrl,
    computed_field,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from acere.constants import DEFAULT_INSTANCE_PATH, ENV_PREFIX
from acere.instances.paths import get_app_path_handler, setup_app_path_handler
from acere.utils.logger import LoggingConf, get_logger

from .app import AppConf
from .epg import EPGInstanceConf
from .scraper import AceScrapeConf

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object
logger = get_logger(__name__)


__all__ = [
    "AceReStreamerConf",
    "AceScrapeConf",
    "AppConf",
    "EPGInstanceConf",
]

setup_app_path_handler(DEFAULT_INSTANCE_PATH)


def parse_cors(v: Any) -> list[str] | str:  # noqa: ANN401 JSON things
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    if isinstance(v, list | str):
        return v
    raise ValueError(v)


class AceReStreamerConf(BaseSettings):
    """Settings Definition."""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env" if not os.getenv("ACERE_TESTING") else None,
        env_prefix=ENV_PREFIX,
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        json_file=get_app_path_handler().settings_file,
    )

    # Default values for our settings
    app: AppConf = AppConf()
    logging: LoggingConf = LoggingConf()
    scraper: AceScrapeConf = AceScrapeConf()
    epgs: list[EPGInstanceConf] = []
    REMOTE_SETTINGS_URL: HttpUrl | None = None
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

    @field_validator("EXTERNAL_URL", mode="after")
    @classmethod
    def validate_external_url(cls, value: str) -> str:
        """Ensure EXTERNAL_URL does not end with a slash."""
        return value.rstrip("/")

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
            config_path = get_app_path_handler().settings_file

        time_str = datetime.now(tz=UTC).strftime("%Y-%m-%d_%H%M%S")
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
            config_path = get_app_path_handler().settings_file

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

    def update_from(self, other: Self) -> None:
        """Update this instance in-place with values from another instance.

        This is useful for updating a global settings object without replacing
        the reference, so all modules that imported it will see the changes.
        """
        self.__dict__.update(other.__dict__)


class ConfigExport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scraper: AceScrapeConf
    epgs: list[EPGInstanceConf]

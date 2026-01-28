import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from acere.api.deps import (
    get_current_active_superuser,
)
from acere.core.config import AceScrapeConf, EPGInstanceConf
from acere.instances.config import settings


class ConfigExport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scraper: AceScrapeConf
    epgs: list[EPGInstanceConf]


router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/", dependencies=[Depends(get_current_active_superuser)])
def get_config() -> ConfigExport:
    """API endpoint to get the current scraper and EPG configuration."""
    return ConfigExport(
        scraper=settings.scraper,
        epgs=settings.epgs,
    )


@router.post("/", dependencies=[Depends(get_current_active_superuser)])
def update_config(config: ConfigExport) -> ConfigExport:
    """API endpoint to update the current scraper and EPG configuration.

    You can send this a full configuration and it will only replace the scraper and the EPGs parts.
    """
    settings.scraper = config.scraper
    settings.epgs = config.epgs
    settings.write_backup_config(
        config_path=None,
        existing_data=json.loads(settings.model_dump_json()),
        reason="Configuration updated via API",
    )
    settings.write_config()
    return ConfigExport(
        scraper=settings.scraper,
        epgs=settings.epgs,
    )

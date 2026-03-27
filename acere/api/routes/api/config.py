from fastapi import APIRouter, Depends

from acere.api.deps import (
    get_current_active_superuser,
)
from acere.config import ConfigExport
from acere.instances.remote_settings import get_remote_settings_fetcher
from acere.services.remote_settings.models import RemoteSettingsGetModel, RemoteSettingsSetModel
from acere.utils.api_models import MessageResponseModel

router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/", dependencies=[Depends(get_current_active_superuser)])
def get_config() -> ConfigExport:
    """API endpoint to get the current scraper and EPG configuration."""
    return get_remote_settings_fetcher().get_export_config()


@router.post("/", dependencies=[Depends(get_current_active_superuser)])
def update_config(config: ConfigExport) -> ConfigExport:
    """API endpoint to update the current scraper and EPG configuration.

    You can send this a full configuration and it will only replace the scraper and the EPGs parts.
    """
    return get_remote_settings_fetcher().update_config_with_export(config)


@router.get("/remote", dependencies=[Depends(get_current_active_superuser)])
def fetch_remote_settings() -> RemoteSettingsGetModel:
    """API endpoint to get the current remote settings URL and flags."""
    return get_remote_settings_fetcher().get_remote_settings_url()


@router.post("/remote", dependencies=[Depends(get_current_active_superuser)])
def trigger_fetch_remote_settings(settings_model: RemoteSettingsSetModel) -> MessageResponseModel:
    """API endpoint to set the remote settings URL and flags."""
    get_remote_settings_fetcher().set_remote_settings_url(
        url=settings_model.url,
        enable_epg=settings_model.enable_epg,
        enable_ace=settings_model.enable_ace,
    )
    return MessageResponseModel(message="Remote settings updated and fetching started.")


@router.post("/reload", dependencies=[Depends(get_current_active_superuser)])
def reload_config() -> MessageResponseModel:
    """API endpoint to refresh the configuration."""
    get_remote_settings_fetcher().reload_config()
    return MessageResponseModel(message="Configuration refresh triggered.")

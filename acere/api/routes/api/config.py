from fastapi import APIRouter

from acere.core.config import ConfigExport
from acere.instances.remote_settings import get_remote_settings_fetcher
from acere.services.remote_settings.models import RemoteSettingsURLGetModel, RemoteSettingsURLSetModel
from acere.utils.api_models import MessageResponseModel

router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/")
def get_config() -> ConfigExport:
    """API endpoint to get the current scraper and EPG configuration."""
    return get_remote_settings_fetcher().get_export_config()


@router.post("/")
def update_config(config: ConfigExport) -> ConfigExport:
    """API endpoint to update the current scraper and EPG configuration.

    You can send this a full configuration and it will only replace the scraper and the EPGs parts.
    """
    return get_remote_settings_fetcher().update_config_with_export(config)


@router.get("/remote")
def fetch_remote_settings() -> RemoteSettingsURLGetModel:
    """API endpoint to get the current remote settings URL."""
    return get_remote_settings_fetcher().get_remote_settings_url()


@router.post("/remote")
def trigger_fetch_remote_settings(url_model: RemoteSettingsURLSetModel) -> MessageResponseModel:
    """API endpoint to set the remote settings URL."""
    get_remote_settings_fetcher().set_remote_settings_url(url_model.url)
    return MessageResponseModel(message="Remote settings URL updated and fetching started.")


@router.post("/reload")
def reload_config() -> MessageResponseModel:
    """API endpoint to refresh the configuration."""
    get_remote_settings_fetcher().reload_config()
    return MessageResponseModel(message="Configuration refresh triggered.")

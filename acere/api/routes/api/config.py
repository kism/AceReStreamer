"""Blueprints for admin API, requires app context."""

from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException

from acere.api.deps import get_current_user
from acere.core.config import AceReStreamerConf
from acere.instances.config import settings
from acere.utils.api_models import MessageResponseModel

router = APIRouter(
    prefix="/config",
    tags=["Configuration"],
    dependencies=[Depends(get_current_user)],
)


# region Config Loader
@router.get("/")
def get_config() -> AceReStreamerConf:
    """API endpoint to get the current config."""
    settings_temp = settings.model_copy()
    settings_temp.SECRET_KEY = ""
    settings_temp.FIRST_SUPERUSER_PASSWORD = ""
    return settings_temp


@router.post("/")
def load_config(body_json: Annotated[dict[Any, Any], Body()]) -> MessageResponseModel:
    """API endpoint to load a new config."""
    if not body_json:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=MessageResponseModel(message="json is empty"),
        )

    if not body_json:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=MessageResponseModel(message="json is empty"),
        )

    new_conf = AceReStreamerConf(**body_json)

    settings = new_conf
    settings.write_config()

    return MessageResponseModel(message="Config reloaded successfully")

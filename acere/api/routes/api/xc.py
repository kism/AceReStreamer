"""Blueprint for IPTV functionality in Ace Streamer."""

from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import HttpUrl

from acere.constants import OUR_TIMEZONE
from acere.database.handlers.category_xc import CategoryXCCategoryIDDatabaseHandler
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.config import settings
from acere.services.xc.helpers import (
    check_xc_auth,
    get_expiry_date,
    get_port_and_protocol_from_external_url,
)
from acere.services.xc.models import (
    XCApiResponse,
    XCCategory,
    XCServerInfo,
    XCStream,
    XCUserInfo,
)
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Xtream Codes"])
category_xc_category_id_mapping = CategoryXCCategoryIDDatabaseHandler()


def _populate_xc_api_response(
    username: str,
    password: str,
) -> XCApiResponse:
    """Populate the XC API response with user and server information."""
    external_url = HttpUrl(settings.EXTERNAL_URL)

    http_port, https_port, protocol = get_port_and_protocol_from_external_url(external_url)

    return XCApiResponse(
        user_info=XCUserInfo(
            username=username,
            password=password,
            exp_date=get_expiry_date(),
        ),
        server_info=XCServerInfo(
            url=external_url,
            port=http_port,
            https_port=https_port,
            server_protocol=protocol,
            timestamp_now=int(datetime.now(tz=UTC).timestamp()),
            time_now=datetime.now(tz=OUR_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


# region /player_api.php
@router.get(
    "/player_api.php",
    responses={
        200: {
            "description": "XC API Response depending on action parameter. XCApiResponse, list[XCCategory], list[XCStream]",  # noqa: E501
        },
    },
    response_model=None,
)
def xc_iptv_router(
    action: str = "",
    username: str = "",
    password: str = "",
    category_id: str = "",
) -> XCApiResponse | list[XCCategory] | list[XCStream]:
    """Route XC API requests to appropriate handlers.

    Actions: get_live_categories, get_live_streams, get_vod_categories, get_vod_streams, get_series_categories, get_series.
    """  # noqa: E501
    stream_token = check_xc_auth(username=username, stream_token=password)

    if action == "get_live_categories":
        return _get_live_categories()
    if action == "get_live_streams":
        return _get_live_streams(category_id, token=password)
    if action in [
        "get_vod_categories",
        "get_vod_streams",
        "get_series_categories",
        "get_series",
    ]:
        raise HTTPException(
            status_code=HTTPStatus.NOT_IMPLEMENTED,
            detail=f"Action '{action}' is not implemented",
        )
    if action != "":
        logger.error("XC client tried an unknown action '%s' in /player_api.php", action)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Unknown action '{action}'",
        )
    return _populate_xc_api_response(username=username, password=stream_token)


def _get_live_categories() -> list[XCCategory]:
    """Get live TV categories."""
    # Get all the categories that are actually in use
    handler = get_ace_streams_db_handler()
    categories_in_use = {stream.category_id for stream in handler.get_streams_as_iptv_xc(None)}
    # Convert them to integers because the XC 'spec' says they should be strings, despite being numeric
    categories_in_use_int = {int(cat_id) for cat_id in categories_in_use if cat_id.isdigit()}
    # Get a list of XCCategory objects
    return category_xc_category_id_mapping.get_all_categories_api(categories_in_use_int)


def _get_live_streams(category_id: str, token: str) -> list[XCStream]:
    """Get live TV streams."""
    handler = get_ace_streams_db_handler()
    xc_category = int(category_id) if category_id.isdigit() else None
    return handler.get_streams_as_iptv_xc(xc_category, token=token)


def _get_unknown_action(action: str) -> MessageResponseModel:
    """Handle unknown actions."""
    logger.warning("Unknown action '%s' in /player_api.php", action)
    return MessageResponseModel(message="Unknown action")


# endregion /player_api.php


# region /status.php
@router.get("/get.php", response_model=None)
def xc_get(
    username: Annotated[str, Query(alias="username")] = "",
    password: Annotated[str, Query(alias="password")] = "",
    type_: Annotated[str, Query(alias="type")] = "",  # Fastapi fixes this as type is a reserved word
) -> Response | MessageResponseModel:
    """Emulate an XC /get.php endpoint."""
    stream_token = check_xc_auth(username=username, stream_token=password)

    if type_ == "m3u_plus":
        return _get_m3u_plus(token=stream_token)

    return _get_invalid_request_type()


def _get_m3u_plus(token: str) -> Response:
    """Get M3U playlist."""
    handler = get_ace_streams_db_handler()
    m3u8 = handler.get_streams_as_iptv(token=token)
    return Response(
        content=m3u8,
        status_code=HTTPStatus.OK,
        media_type="application/vnd.apple.mpegurl",
    )


def _get_invalid_request_type() -> MessageResponseModel:
    """Handle invalid request types."""
    return MessageResponseModel(message="Invalid request type", errors=["Expected: 'type=m3u_plus'"])


# endregion /status.php

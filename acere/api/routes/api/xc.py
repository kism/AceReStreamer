"""Blueprint for IPTV functionality in Ace Streamer."""

from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import HttpUrl

from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.config import settings
from acere.instances.iptv_streams import get_iptv_streams_db_handler
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
            time_now=datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
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
    check_xc_auth(username=username, stream_token=password)

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
    return _populate_xc_api_response(username=username, password=password)


def _get_live_categories() -> list[XCCategory]:
    """Get live TV categories from both ace and IPTV proxy streams."""
    ace_categories = get_ace_streams_db_handler().get_xc_categories()
    iptv_categories = get_iptv_streams_db_handler().get_xc_categories()

    # Merge, deduplicating by category_id
    seen: set[int] = set()
    merged: list[XCCategory] = []
    for cat in ace_categories + iptv_categories:
        if cat.category_id not in seen:
            seen.add(cat.category_id)
            merged.append(cat)
    return merged


def _get_live_streams(category_id: str, token: str) -> list[XCStream]:
    """Get live TV streams from both ace and IPTV proxy."""
    xc_category = int(category_id) if category_id and category_id.isdigit() else None

    ace_streams = get_ace_streams_db_handler().get_streams_as_iptv_xc(xc_category, token=token)
    iptv_streams = get_iptv_streams_db_handler().get_streams_as_iptv_xc(xc_category, token=token)

    # Re-number sequentially across both lists
    combined = ace_streams + iptv_streams
    for i, stream in enumerate(combined, start=1):
        stream.num = i

    return combined


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
    """Get combined M3U playlist (ace + IPTV proxy)."""
    external_url = settings.EXTERNAL_URL
    epg_url_str = f"{external_url}/epg.xml"
    if token:
        epg_url_str += f"?token={token}"
    epg_url = HttpUrl(epg_url_str)
    m3u8_header = f'#EXTM3U x-tvg-url="{epg_url}" url-tvg="{epg_url}" refresh="3600"\n'

    ace_lines = get_ace_streams_db_handler().get_iptv_lines(token=token)
    iptv_lines = get_iptv_streams_db_handler().get_iptv_lines(token=token)

    all_lines = sorted(set(ace_lines + iptv_lines))
    m3u8 = m3u8_header + "\n".join(all_lines)

    return Response(
        content=m3u8,
        status_code=HTTPStatus.OK,
        media_type="application/vnd.apple.mpegurl",
    )


def _get_invalid_request_type() -> MessageResponseModel:
    """Handle invalid request types."""
    return MessageResponseModel(message="Invalid request type", errors=["Expected: 'type=m3u_plus'"])


# endregion /status.php

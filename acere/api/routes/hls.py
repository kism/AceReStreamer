"""Stream Handling Blueprint."""

from http import HTTPStatus
from typing import Annotated

import aiohttp
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import HttpUrl

from acere.constants import STATIC_DIR, TVG_LOGOS_DIR
from acere.core.stream_token import verify_stream_token
from acere.instances.ace_pool import get_ace_pool
from acere.instances.ace_quality import get_quality_handler
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.config import settings
from acere.services.xc.helpers import check_xc_auth
from acere.utils.api_models import MessageResponseModel
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.hls import (
    replace_hls_m3u_sources,
)
from acere.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Media/Stream"])

REVERSE_PROXY_EXCLUDED_HEADERS = [
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas


# region /hls/
@router.get("/hls/{path}", response_class=Response)
async def hls(  # noqa: PLR0915 This is hell
    path: str,
    token: str = "",
    *,
    authentication_override: bool = False,
) -> Response:
    """Reverse proxy the HLS from Ace."""
    if not authentication_override:
        verify_stream_token(token)

    ace_pool = get_ace_pool()

    if not check_valid_content_id_or_infohash(path):
        msg = f"Invalid content ID or infohash: {path}"
        logger.error("HLS stream error: %s", msg)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=msg,
        )

    instance_ace_hls_m3u8_url = await ace_pool.get_instance_hls_url_by_content_id(path)

    if not instance_ace_hls_m3u8_url:
        msg = f"Can't serve hls_stream, Ace pool is full or invalid stream: {path}"
        logger.error("HLS stream error: %s", msg)
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail=msg,
        )

    logger.trace("HLS stream requested for path: %s", instance_ace_hls_m3u8_url)

    try:
        timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(instance_ace_hls_m3u8_url.encoded_string()) as ace_resp:
                ace_resp.raise_for_status()
                content_bytes = await ace_resp.read()
                status_code = ace_resp.status
                headers = ace_resp.headers
    except (aiohttp.ClientError, TimeoutError) as e:
        error_short = type(e).__name__

        # Get the HTTP status code from ace if available
        if isinstance(e, aiohttp.ClientResponseError):
            status_info = f" (ace status: {e.status} {e.message})"
        elif isinstance(e, TimeoutError):
            status_info = f" (timeout: {REVERSE_PROXY_TIMEOUT}s)"
        else:
            status_info = " (???)"

        # Determine error type and response
        if isinstance(e, (aiohttp.ServerTimeoutError, TimeoutError)):
            logger.error("reverse proxy timeout /hls/%s %s%s", path, error_short, status_info)
            error_msg, status = "HLS stream timeout", HTTPStatus.REQUEST_TIMEOUT
            get_quality_handler().increment_quality(path, "")
        elif isinstance(e, aiohttp.ClientConnectionError):
            logger.error("%s reverse proxy cannot connect to Ace%s", error_short, status_info)
            error_msg, status = (
                "Cannot connect to Ace",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        else:
            logger.error("reverse proxy failure /hls/ %s%s", error_short, status_info)
            error_msg, status = (
                f"Failed to fetch HLS stream{status_info}",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            get_quality_handler().increment_quality(path, "")

        raise HTTPException(status_code=status, detail=error_msg) from e

    content_str = content_bytes.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS stream received for path: %s", path)
        logger.debug("Content received: %s", content_str[:1000])
        get_quality_handler().increment_quality(path, "")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Invalid HLS stream for {content_str}",
        )

    content_str = replace_hls_m3u_sources(
        m3u_content=content_str,
        ace_address=settings.app.ace_address,
        server_name=HttpUrl(settings.EXTERNAL_URL),
        token=token,
    )

    get_quality_handler().increment_quality(path, m3u_playlist=content_str)

    resp = Response(content_str, status_code)
    resp.headers.update(
        {name: value for (name, value) in headers.items() if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS}
    )
    return resp


# region /hls/m/
# Taking the easy route and capturing the full following path
@router.get("/hls/m/{path:path}", response_class=Response)
async def hls_multi(path: str, token: str = "") -> Response:
    """Reverse proxy the HLS multistream from Ace."""
    verify_stream_token(token)

    ace_pool = get_ace_pool()

    content_id = ace_pool.get_instance_by_multistream_path(path)

    url = HttpUrl(
        f"{settings.app.ace_address.encoded_string()}hls/m/{path}"
    ).encoded_string()  # This will deduplicate slashes

    try:
        timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as ace_resp:
                ace_resp.raise_for_status()
                content_bytes = await ace_resp.read()
                status_code = ace_resp.status
    except (aiohttp.ClientError, TimeoutError) as e:
        error_short = type(e).__name__
        logger.error("reverse proxy failure /hls/m/ %s", error_short)
        error_msg = "Failed to fetch HLS multistream"

        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error_msg) from e

    content_str = content_bytes.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS stream received for path: %s", path)
        logger.debug("Content received: %s", content_str[:1000])
        get_quality_handler().increment_quality(content_id, "")
        response_body = MessageResponseModel(message="Invalid HLS stream", errors=[content_str]).model_dump_json()
        return Response(
            content=response_body,
            media_type="application/json",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    content_str = replace_hls_m3u_sources(
        m3u_content=content_str,
        ace_address=settings.app.ace_address,
        server_name=HttpUrl(settings.EXTERNAL_URL),
        token=token,
    )

    get_quality_handler().increment_quality(content_id, m3u_playlist=content_str)

    return Response(content_str, status_code)


# region XC
# Depending on the Client, it will either be:
# /live/u/p/<xc_id>.m3u8  | UHF, M3UAndroid, IPTV Smarters Pro
# /u/p/<xc_id>            | Smarters Player Lite (iOS), iMPlayer Android
# /u/p/<xc_id>.ts         | iMPlayer iOS, TiViMate, Purple Simple (okay that m3u8 is the response)
# /u/p/<tvg_id>.m3u8      | SparkleTV
@router.get("/{_path_username}/{_path_password}/{xc_stream}", response_class=Response)
@router.get("/live/{_path_username}/{_path_password}/{xc_stream}", response_class=Response)
async def xc_m3u8(
    request: Request,
    _path_username: str = "",
    _path_password: str = "",
    xc_stream: str = "",
    password: Annotated[str, Query(alias="password")] = "",
    username: Annotated[str, Query(alias="username")] = "",
) -> Response:
    """Serve the XC m3u8 file for Ace content."""
    # Who knows if it makes it more efficent
    # the non-path query params do show up sometimes
    # maybe i'll need them in the future
    username = _path_username or username
    password = _path_password or password

    stream_token = check_xc_auth(username=username, stream_token=password)

    content_id: str | None = None

    logger.trace(
        "XC HLS: path='%s' args='%s' ua='%s'",
        str(request.url) if request else xc_stream,
        f"username={username},password={password}",
        request.headers.get("User-Agent", "") if request else "",
    )

    xc_id_clean = xc_stream.split(".", 1)[0]  # Remove file extension if present

    try:
        xc_id_int = int(xc_id_clean)
    except ValueError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Client requested invalid XC ID: {xc_stream} -> {xc_id_clean}",
        ) from None

    content_id = get_ace_streams_db_handler().get_content_id_by_xc_id(xc_id_int)

    if content_id is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid XC ID format")

    if not content_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Content ID not found for the given XC ID",
        )

    return await hls(content_id, stream_token)


# region /ace/c/ and /hls/c/ Content paths for regular and multistream
# Do a full path capture here, since ace puts a bunch of stuff following
@router.get("/ace/c/{path:path}", response_class=Response, name="ace_content_1")
@router.get("/hls/c/{path:path}", response_class=Response, name="ace_content_2")
async def ace_content(path: str, request: Request, token: str = "") -> Response:
    """Reverse proxy the Ace content."""
    verify_stream_token(token)

    # Determine the correct URL based on the request path
    if "/hls/c/" in request.url.path:
        url = HttpUrl(f"{settings.app.ace_address}hls/c/{path}").encoded_string()
        route_prefix = "/hls/c/"
    else:
        url = HttpUrl(f"{settings.app.ace_address}ace/c/{path}").encoded_string()
        route_prefix = "/ace/c/"

    logger.trace("Ace content requested for url: %s", url)

    try:
        timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                content = await resp.read()
                status_code = resp.status
                response_headers = resp.headers
    except (aiohttp.ServerTimeoutError, TimeoutError) as e:
        error_short = type(e).__name__
        logger.error(
            "%s reverse proxy timeout %s",
            route_prefix,
            error_short,
        )
        response_body = MessageResponseModel(message="Ace content timeout").model_dump_json()
        return Response(
            content=response_body,
            media_type="application/json",
            status_code=HTTPStatus.REQUEST_TIMEOUT,
        )
    except aiohttp.ClientError as e:
        error_short = type(e).__name__
        logger.error("%s reverse proxy failure %s", route_prefix, error_short)
        response_body = MessageResponseModel(message="Failed to fetch HLS stream").model_dump_json()
        return Response(
            content=response_body,
            media_type="application/json",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    headers = [
        (name, value)
        for (name, value) in response_headers.items()
        if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    response = Response(content=content, status_code=status_code, headers=dict(headers))

    response.headers["Content-Type"] = "video/MP2T"

    return response


# region /tvg-logo/
@router.get("/tvg-logo/{path}", response_class=FileResponse)
def tvg_logo(path: str, token: str = "") -> FileResponse:
    """Serve the TVG logo from the local filesystem."""
    # You'll need to define where static_folder and instance_path come from
    # This might be from settings or app configuration
    verify_stream_token(token)

    # Not sure if this check is needed
    if STATIC_DIR is None:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Static folder not configured",
        )

    logo_path = TVG_LOGOS_DIR / path

    if not logo_path.is_file():
        default_logo = STATIC_DIR / "default_tvg_logo.png"
        return FileResponse(
            path=default_logo,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    return FileResponse(path=logo_path, headers={"Cache-Control": "public, max-age=3600"})

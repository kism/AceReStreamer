"""HLS stream handling routes — shared constants, XC dispatch, and tvg-logo."""

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse

from acere.constants import STATIC_DIR
from acere.core.stream_token import verify_stream_token
from acere.instances.paths import get_app_path_handler
from acere.instances.xc_stream_map import get_xc_stream_map_handler
from acere.services.xc.helpers import check_xc_auth
from acere.utils.logger import get_logger

from .ace import hls
from .ace import router as ace_router
from .iptv import hls_web
from .iptv import router as iptv_router

logger = get_logger(__name__)

REVERSE_PROXY_EXCLUDED_HEADERS = [
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas

router = APIRouter(tags=["Media/Stream"])

# Include specific routes first — order matters so they match before the XC catch-all
router.include_router(ace_router)
router.include_router(iptv_router)


# region XC
# Depending on the Client, it will either be:
# /live/u/p/<xc_id>.m3u8  | UHF, M3UAndroid, IPTV Smarters Pro
# /u/p/<xc_id>            | Smarters Player Lite (iOS), iMPlayer Android
# /u/p/<xc_id>.ts         | iMPlayer iOS, TiViMate, Purple Simple (okay that m3u8 is the response)
# /u/p/<xc_id>.m3u8      | SparkleTV
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
    """Serve the XC m3u8 file for any stream type."""
    # Who knows if it makes it more efficent
    # the non-path query params do show up sometimes
    # maybe i'll need them in the future
    username = _path_username or username
    password = _path_password or password

    stream_token = check_xc_auth(username=username, stream_token=password)

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

    stream_info = get_xc_stream_map_handler().get_stream_info_by_xc_id(xc_id_int)

    if stream_info is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="XC ID not found in stream map",
        )

    stream_type, stream_key = stream_info

    if stream_type == "ace":
        return await hls(stream_key, stream_token)
    if stream_type == "iptv":
        return await hls_web(request, stream_key, stream_token)

    raise HTTPException(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        detail=f"Unknown stream type in xc_stream_map: {stream_type}",
    )


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

    logo_path = get_app_path_handler().tvg_logos_dir / path

    if not logo_path.is_file():
        default_logo = STATIC_DIR / "default_tvg_logo.png"
        return FileResponse(
            path=default_logo,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    return FileResponse(path=logo_path, headers={"Cache-Control": "public, max-age=3600"})

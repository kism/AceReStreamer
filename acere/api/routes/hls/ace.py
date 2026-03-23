"""Ace HLS stream handling routes."""

from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import HttpUrl

from acere.core.stream_token import verify_stream_token
from acere.instances.ace_pool import get_ace_pool
from acere.instances.ace_quality import get_quality_handler
from acere.instances.config import settings
from acere.utils.api_models import MessageResponseModel
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.hls import replace_hls_m3u_sources
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
else:
    AsyncGenerator = object

logger = get_logger(__name__)

router = APIRouter()

REVERSE_PROXY_EXCLUDED_HEADERS = [
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas


# region /hls/
@router.get("/hls/ace/{path}", response_class=Response)
async def hls(
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
        log_aiohttp_exception(logger, f"[ace hls {path}]", e)

        # Determine error type and response
        if isinstance(e, (TimeoutError)):
            error_msg, status = "HLS stream timeout", HTTPStatus.REQUEST_TIMEOUT
            get_quality_handler().increment_quality(path, "")
        elif isinstance(e, aiohttp.ClientError):
            error_msg, status = (
                "Cannot connect to Ace",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        else:
            error_msg, status = (
                "Failed to fetch HLS stream",
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
        ace_address=settings.ace.ace_address,
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
@router.get("/hls/ace/m/{path:path}", response_class=Response)
async def hls_multi(path: str, token: str = "") -> Response:
    """Reverse proxy the HLS multistream from Ace."""
    verify_stream_token(token)

    ace_pool = get_ace_pool()

    content_id = ace_pool.get_instance_by_multistream_path(path)

    url = HttpUrl(
        f"{settings.ace.ace_address.encoded_string()}hls/ace/m/{path}"
    ).encoded_string()  # This will deduplicate slashes

    try:
        timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as ace_resp:
                ace_resp.raise_for_status()
                content_bytes = await ace_resp.read()
                status_code = ace_resp.status
    except (aiohttp.ClientError, TimeoutError) as e:
        error_msg = "Failed to fetch HLS multistream"
        log_aiohttp_exception(logger, url, e, error_msg)

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
        ace_address=settings.ace.ace_address,
        server_name=HttpUrl(settings.EXTERNAL_URL),
        token=token,
    )

    get_quality_handler().increment_quality(content_id, m3u_playlist=content_str)

    return Response(content_str, status_code)


# region /ace/c/ and /hls/c/ Content paths for regular and multistream
# Do a full path capture here, since ace puts a bunch of stuff following
@router.get("/ace/c/{path:path}", response_class=Response, name="ace_content_1")
@router.get("/hls/c/{path:path}", response_class=Response, name="ace_content_2")
async def ace_content(path: str, request: Request, token: str = "") -> Response:
    """Reverse proxy the Ace content."""
    verify_stream_token(token)

    # Determine the correct URL based on the request path
    if "/hls/c/" in request.url.path:
        url = HttpUrl(f"{settings.ace.ace_address}hls/c/{path}").encoded_string()
    else:
        url = HttpUrl(f"{settings.ace.ace_address}ace/c/{path}").encoded_string()

    logger.trace("Ace content requested for url: %s", url)

    timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
    session = aiohttp.ClientSession(timeout=timeout)
    try:
        resp = await session.get(url)
        resp.raise_for_status()
    except (aiohttp.ClientError, TimeoutError) as e:
        await session.close()
        log_aiohttp_exception(logger, url, e)
        response_body = MessageResponseModel(message="Ace content timeout").model_dump_json()

        if isinstance(e, TimeoutError):
            return Response(
                content=response_body,
                media_type="application/json",
                status_code=HTTPStatus.REQUEST_TIMEOUT,
            )
        return Response(
            content=response_body,
            media_type="application/json",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    headers = [
        (name, value)
        for (name, value) in resp.headers.items()
        if name.lower() not in {*REVERSE_PROXY_EXCLUDED_HEADERS, "content-type"}
    ]

    async def generate() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in resp.content.iter_chunked(65536):
                yield chunk
        finally:
            resp.close()
            await session.close()

    return StreamingResponse(generate(), status_code=resp.status, headers=dict(headers), media_type="video/MP2T")

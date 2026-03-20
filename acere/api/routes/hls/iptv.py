"""IPTV proxy HLS stream handling routes."""

from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from acere.core.stream_token import verify_stream_token
from acere.instances.config import settings
from acere.instances.iptv_proxy import get_iptv_proxy_manager
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.hls import rewrite_iptv_hls_segments
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


# region /hls/web/
@router.get("/hls/web/{slug}", response_class=Response)
async def hls_web(slug: str, token: str = "") -> Response:
    """Reverse proxy an upstream IPTV HLS playlist, rewriting segment URLs."""
    verify_stream_token(token)

    iptv_manager = get_iptv_proxy_manager()
    upstream_url = iptv_manager.get_upstream_url(slug)

    if not upstream_url:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Unknown IPTV stream: {slug}",
        )

    try:
        timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(upstream_url) as resp:
                resp.raise_for_status()
                content_bytes = await resp.read()
                status_code = resp.status
                headers = resp.headers
    except (aiohttp.ClientError, TimeoutError) as e:
        log_aiohttp_exception(logger, f"[iptv hls {slug}]", e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail="Failed to fetch upstream IPTV stream",
        ) from e

    content_str = content_bytes.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS content received for IPTV slug: %s", slug)
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail="Upstream did not return valid HLS content",
        )

    content_str = rewrite_iptv_hls_segments(
        m3u_content=content_str,
        slug=slug,
        server_name=settings.EXTERNAL_URL,
    )

    resp_out = Response(content=content_str, status_code=status_code)
    resp_out.headers.update(
        {name: value for name, value in headers.items() if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS}
    )

    return resp_out


# region /hls/web-segment/
@router.get("/hls/web-segment/{slug}/{segment:path}", response_class=Response)
async def hls_web_segment(slug: str, segment: str) -> Response:
    """Proxy an upstream IPTV segment. No token required (nginx caching)."""
    iptv_manager = get_iptv_proxy_manager()
    segment_url = iptv_manager.get_segment_upstream_url(slug, segment)

    if not segment_url:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Unknown IPTV stream slug: {slug}",
        )

    timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
    session = aiohttp.ClientSession(timeout=timeout)
    try:
        resp = await session.get(segment_url)
        resp.raise_for_status()
    except (aiohttp.ClientError, TimeoutError) as e:
        await session.close()
        log_aiohttp_exception(logger, segment_url, e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail="Failed to fetch upstream segment",
        ) from e

    headers = [
        (name, value) for name, value in resp.headers.items() if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    async def generate() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in resp.content.iter_chunked(65536):
                yield chunk
        finally:
            resp.close()
            await session.close()

    return StreamingResponse(generate(), status_code=resp.status, headers=dict(headers), media_type="video/MP2T")

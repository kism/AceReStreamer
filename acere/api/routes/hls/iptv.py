"""IPTV proxy HLS stream handling routes."""

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from acere.core.stream_token import verify_stream_token
from acere.instances.config import settings
from acere.instances.iptv_proxy import get_iptv_proxy_manager
from acere.instances.iptv_streams import get_iptv_streams_db_handler
from acere.instances.quality import get_quality_handler
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.hls import rewrite_iptv_hls_segments
from acere.utils.logger import get_logger
from acere.utils.m3u8_fetch_cache import FetchCache

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


@dataclass
class _PlaylistFetch:
    content: bytes
    status: int
    headers: dict[str, str]
    final_url: str


_playlist_cache: FetchCache[_PlaylistFetch] = FetchCache(ttl=3.0)


async def _fetch_playlist(url: str) -> _PlaylistFetch:
    timeout = aiohttp.ClientTimeout(total=REVERSE_PROXY_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, allow_redirects=True) as resp:
            resp.raise_for_status()
            return _PlaylistFetch(
                content=await resp.read(),
                status=resp.status,
                headers=dict(resp.headers),
                final_url=str(resp.url),
            )


# region /hls/web/
@router.get("/hls/web/{slug}", response_class=Response)
async def hls_web(slug: str, token: str = "") -> Response:
    """Reverse proxy an upstream IPTV HLS playlist, rewriting segment URLs."""
    verify_stream_token(token)

    iptv_manager = get_iptv_proxy_manager()

    # Pool enforcement — check if this source has capacity
    if not iptv_manager.check_stream_allowed(slug):
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="IPTV source stream limit reached, all active streams are locked in",
        )

    upstream_url = iptv_manager.get_upstream_url(slug)

    if not upstream_url:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Unknown IPTV stream: {slug}",
        )

    # Get canonical upstream URL from DB for quality tracking (stable, not affected by redirects)
    db_entry = get_iptv_streams_db_handler().get_by_slug(slug)
    quality_hls_identifier = db_entry.upstream_url if db_entry else upstream_url

    try:
        fetched = await _playlist_cache.get(upstream_url, _fetch_playlist)
    except (aiohttp.ClientError, TimeoutError) as e:
        log_aiohttp_exception(logger, f"[iptv hls {slug}] -> {upstream_url}", e)
        get_quality_handler().increment_quality(quality_hls_identifier, "")
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail="Failed to fetch upstream IPTV stream",
        ) from e

    # If the upstream redirected, update the URL map so segment requests use the correct base
    if fetched.final_url != upstream_url:
        logger.debug("IPTV slug %s redirected: %s -> %s", slug, upstream_url, fetched.final_url)
        iptv_manager.update_upstream_url(slug, fetched.final_url)

    content_str = fetched.content.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS content received for IPTV slug: %s", slug)
        get_quality_handler().increment_quality(quality_hls_identifier, "")
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail="Upstream did not return valid HLS content",
        )

    content_str = rewrite_iptv_hls_segments(
        m3u_content=content_str,
        slug=slug,
        server_name=settings.EXTERNAL_URL,
    )

    get_quality_handler().increment_quality(quality_hls_identifier, content_str)

    resp_out = Response(content=content_str, status_code=fetched.status)
    resp_out.headers.update(
        {name: value for name, value in fetched.headers.items() if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS}
    )

    return resp_out


# region /hls/web-segment/
@router.get("/hls/web-segment/{slug}/{segment:path}", response_class=Response)
async def hls_web_segment(slug: str, segment: str) -> Response:
    """Proxy an upstream IPTV segment. No token required (nginx caching)."""
    iptv_manager = get_iptv_proxy_manager()

    # Update last-used for pool tracking
    iptv_manager.pool.touch(slug)

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
        log_aiohttp_exception(logger, f"[iptv hls segment {slug}/{segment}] -> {segment_url}", e)
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

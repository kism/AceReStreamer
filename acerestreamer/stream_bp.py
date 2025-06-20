"""Main Stream Site Blueprint."""

import re
from http import HTTPStatus
from pathlib import Path

import requests
from flask import Blueprint, Response, jsonify, redirect, render_template, request
from flask_caching import CachedResponse
from werkzeug.wrappers import Response as WerkzeugResponse

from .ace_pool import AcePool
from .authentication_bp import get_ip_from_request, is_ip_allowed
from .authentication_helpers import assumed_auth_failure
from .flask_helpers import DEFAULT_CACHE_DURATION, cache, get_current_app
from .html_snippets import get_header_snippet
from .logger import get_logger
from .scraper import AceScraper
from .scraper_helpers import get_streams_as_iptv
from .stream_helpers import replace_m3u_sources

logger = get_logger(__name__)  # Create a logger: acerestreamer.this_module_name, inherit config from root logger

bp = Blueprint("acerestreamer_scraper", __name__)
ace_scraper: AceScraper = AceScraper(ace_scrape_settings=None, instance_path=None)
ace_pool: AcePool = AcePool(ace_addresses=[])
current_app = get_current_app()

REVERSE_PROXY_EXCLUDED_HEADERS = ["content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive"]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas


def start_scraper() -> None:
    """Method to 'configure' this module. Needs to be called under `with app.app_context():` from __init__.py."""
    global ace_scraper  # noqa: PLW0603 Necessary evil as far as I can tell, could move to all objects but eh...
    global ace_pool  # noqa: PLW0603 Necessary evil as far as I can tell, could move to all objects but eh...

    ace_scraper = AceScraper(current_app.aw_conf.scraper, Path(current_app.instance_path))

    ace_pool = AcePool(current_app.aw_conf.app.ace_addresses)


@bp.route("/")
def home() -> Response | WerkzeugResponse:
    """Render the home page, redirect to stream if IP is allowed."""
    ip_is_allowed = is_ip_allowed(get_ip_from_request())
    if ip_is_allowed:
        return redirect("/stream")

    return redirect("/login")


@bp.route("/stream")
@cache.cached()
def webplayer_stream() -> Response | WerkzeugResponse | CachedResponse:
    """Render the webpage for a stream."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return CachedResponse(  # type: ignore[no-untyped-call] # Missing from flask-caching
        response=Response(
            render_template(
                "stream.html.j2",
                rendered_header=get_header_snippet("Ace ReStreamer"),
            ),
            HTTPStatus.OK,
        ),
        timeout=DEFAULT_CACHE_DURATION,
    )


@bp.route("/iptv")
@bp.route("/iptv.m3u")
@bp.route("/iptv.m3u8")
def iptv() -> Response | WerkzeugResponse:
    """Render the IPTV page."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_flat()
    hls_path = current_app.config["SERVER_NAME"] + "/hls/"
    m3u8 = get_streams_as_iptv(streams=streams, hls_path=hls_path, instance_path=Path(current_app.instance_path))

    return Response(
        m3u8,
        HTTPStatus.OK,
        mimetype="application/vnd.apple.mpegurl",
    )


@bp.route("/hls/<path:path>")
def hls_stream(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the HLS from Ace."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    ace_address = ace_pool.get_instance(path)

    url = f"{ace_address}/ace/manifest.m3u8?content_id={path}"

    logger.trace("HLS stream requested for path: %s", path)

    try:
        resp = requests.get(url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
    except requests.Timeout as e:
        error_short = type(e).__name__
        logger.error("/hls/ reverse proxy timeout %s", error_short)  # noqa: TRY400 Too verbose otherwise
        ace_scraper.increment_quality(path, -5)
        return jsonify({"error": "HLS stream timeout"}, HTTPStatus.REQUEST_TIMEOUT)
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("/hls/ reverse proxy failure %s", error_short)  # noqa: TRY400 Naa this should be shorter
        ace_scraper.increment_quality(path, -5)
        return jsonify({"error": "Failed to fetch HLS stream"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    content_str = resp.content.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS stream received for path: %s", path)
        ace_scraper.increment_quality(path, -5)
        return jsonify({"error": "Invalid HLS stream", "m3u8": content_str}, HTTPStatus.BAD_REQUEST)

    content_str = replace_m3u_sources(m3u_content=content_str, path=path, ace_pool=ace_pool)

    ace_scraper.increment_quality(path, 1)

    return Response(content_str, resp.status_code, headers)


@bp.route("/ace/c/<path:path>")
def ace_content(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the Ace content."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    path_filtered = re.search(r"^([a-f0-9]+)", path)
    if not path_filtered:
        logger.error("Invalid Ace content path: %s", path)
        return jsonify({"error": "Invalid Ace content path"}, HTTPStatus.BAD_REQUEST)
    ace_content_path_filtered = path_filtered.group(1)

    ace_address = ace_pool.get_instance_by_content_path(ace_content_path_filtered)

    if not ace_address:
        response = jsonify({"error": "Ace content not ready"}, HTTPStatus.SERVICE_UNAVAILABLE)
        response.headers["Retry-After"] = "10"
        return response

    url = f"{ace_address}/ace/c/{path}"

    logger.trace("Ace content requested for path: %s", path)

    try:
        resp = requests.get(url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("/ace/c/ reverse proxy failure %s", error_short)  # noqa: TRY400 Naa this should be shorter
        return jsonify({"error": "Failed to fetch HLS stream"}, HTTPStatus.INTERNAL_SERVER_ERROR)
    except requests.Timeout as e:
        error_short = type(e).__name__
        logger.error("/ace/c/ reverse proxy timeout %s", error_short)  # noqa: TRY400 Too verbose otherwise
        return jsonify({"error": "Ace content timeout"}, HTTPStatus.REQUEST_TIMEOUT)

    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    response = Response(resp.content, resp.status_code, headers)

    response.headers["Content-Type"] = "video/MP2T"  # Doesn't seem to be necessary

    return response


@bp.route("/api/stream/<path:ace_id>")
def api_stream(ace_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get a specific stream by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    stream = ace_scraper.get_stream_by_ace_id(ace_id)

    response = jsonify(stream.model_dump())
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/flat")
def api_streams_flat() -> Response | WerkzeugResponse:
    """API endpoint to get the flat streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_flat()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/by_source")
def api_streams() -> Response | WerkzeugResponse:
    """API endpoint to get the streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_all_streams_by_source()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/by_source/<source_slug>")
def api_streams_by_source(source_slug: str) -> Response | WerkzeugResponse:
    """API endpoint to get the streams by source slug."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_by_source(source_slug)
    if not streams:
        return jsonify({"error": "No streams found for this source"}, HTTPStatus.NOT_FOUND)

    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/sources")
def api_streams_sources() -> Response | WerkzeugResponse:
    """API endpoint to get the streams sources."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_sources()
    streams_serialized = streams.model_dump()

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/sources/flat")
def api_streams_sources_flat() -> Response | WerkzeugResponse:
    """API endpoint to get the flat streams sources."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_sources_flat()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/source/<source_slug>")
def api_streams_source_by_slug(source_slug: str) -> Response | WerkzeugResponse:
    """API endpoint to get a specific stream source by slug."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    source = ace_scraper.get_streams_source(source_slug)
    if not source:
        return jsonify({"error": "Source not found"}, HTTPStatus.NOT_FOUND)

    response = jsonify(source.model_dump())
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/health")
def api_streams_health() -> Response | WerkzeugResponse:
    """API endpoint to get the streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_health()

    response = jsonify(streams)
    response.status_code = HTTPStatus.OK

    return response


@bp.route("/api/ace_pool")
def api_ace_pool() -> Response | WerkzeugResponse:
    """API endpoint to get the Ace pool."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    pool_list = ace_pool.get_instances_nice()
    pool_list_serialized = [entry.model_dump() for entry in pool_list]

    response = jsonify(pool_list_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace_pool/<path:ace_id>", methods=["GET", "DELETE"])
def api_ace_pool_by_id(ace_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get or delete an Ace pool entry by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    instance_url = ace_pool.get_instance(ace_id)

    if instance_url is None:
        logger.error("Ace ID %s not found in pool", ace_id)
        return jsonify({"error": "Ace ID not found"}, HTTPStatus.NOT_FOUND)

    if request.method == "GET":
        return jsonify({"ace_url": instance_url}, HTTPStatus.OK)

    if request.method == "DELETE":
        ace_pool.clear_instance_by_ace_id(ace_id)  # Assume success since we validated above
        return jsonify({"message": "Ace ID removed successfully"}, HTTPStatus.OK)

    return jsonify({"error": "Method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)

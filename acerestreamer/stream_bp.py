"""Main Stream Site Blueprint."""

import re
from http import HTTPStatus
from pathlib import Path

import requests
from flask import Blueprint, Response, jsonify, redirect, render_template
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

logger = get_logger(__name__)  # Create a logger: acerestreamer.this_module_name, inherit config from root logger

bp = Blueprint("acerestreamer_scraper", __name__)
ace_scraper: AceScraper | None = None
ace_pool: AcePool | None = None
current_app = get_current_app()

REVERSE_PROXY_EXCLUDED_HEADERS = ["content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive"]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas


def start_scraper() -> None:
    """Method to 'configure' this module. Needs to be called under `with app.app_context():` from __init__.py."""
    global ace_scraper  # noqa: PLW0603 Necessary evil as far as I can tell, could move to all objects but eh...
    global ace_pool  # noqa: PLW0603 Necessary evil as far as I can tell, could move to all objects but eh...

    scraper_cache = Path(current_app.instance_path) / "ace_quality_cache.json"
    ace_scraper = AceScraper(current_app.aw_conf.scraper, scraper_cache)

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

    if not ace_scraper:
        logger.error("Scraper object not initialized.")
        return jsonify({"error": "Scraper not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    streams = ace_scraper.get_streams_flat()
    hls_path = current_app.config["SERVER_NAME"] + "/hls/"
    m3u8 = get_streams_as_iptv(streams, hls_path)

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

    if not ace_scraper or not ace_pool:
        logger.error("Scraper or Pool object not initialized.")
        return jsonify({"error": "Scraper not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    ace_address = ace_pool.get_instance(path)

    url = f"{ace_address}/ace/manifest.m3u8?content_id={path}"

    logger.debug("HLS stream requested for path: %s", path)

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

    lines_new = []
    for line in content_str.splitlines():
        line_temp = line.strip()
        if "/ace/c/" in line:
            for address in current_app.aw_conf.app.ace_addresses:
                if line_temp.startswith(address):
                    line_temp = line_temp.replace(address, current_app.config["SERVER_NAME"])

            current_content_identifier = re.search(r"/ace/c/([a-f0-9]+)", line_temp)
            if current_content_identifier:
                ace_pool.set_content_path(ace_id=path, content_path=current_content_identifier.group(1))

        lines_new.append(line_temp)

    content_str = "\n".join(lines_new)

    ace_scraper.increment_quality(path, 1)

    return Response(content_str, resp.status_code, headers)


@bp.route("/ace/c/<path:path>")
def ace_content(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the Ace content."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if not ace_pool:
        return jsonify({"error": "Ace pool not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    path_filtered = re.search(r"^([a-f0-9]+)", path)
    if not path_filtered:
        logger.error("Invalid Ace content path: %s", path)
        return jsonify({"error": "Invalid Ace content path"}, HTTPStatus.BAD_REQUEST)
    ace_content_path_filtered = path_filtered.group(1)

    ace_address = ace_pool.get_instance_by_content_path(ace_content_path_filtered)

    url = f"{ace_address}/ace/c/{path}"

    logger.debug("Ace content requested for path: %s", path)

    try:
        resp = requests.get(url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("/ace/c/ reverse proxy failure %s", error_short)  # noqa: TRY400 Naa this should be shorter
        return jsonify({"error": "Failed to fetch HLS stream"}, HTTPStatus.INTERNAL_SERVER_ERROR)
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

    if not ace_scraper:
        logger.error("Scraper object not initialized.")
        return jsonify({"error": "Scraper not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

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

    if not ace_scraper:
        logger.error("Scraper object not initialized.")
        return jsonify({"error": "Scraper not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    streams = ace_scraper.get_streams_flat()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/by_site")
def api_streams() -> Response | WerkzeugResponse:
    """API endpoint to get the streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if not ace_scraper:
        logger.error("Scraper object not initialized.")
        return jsonify({"error": "Scraper not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    streams = ace_scraper.get_streams()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/health")
def api_streams_health() -> Response | WerkzeugResponse:
    """API endpoint to get the streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if not ace_scraper:
        logger.error("Scraper object not initialized.")
        return jsonify({"error": "Scraper not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

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

    if not ace_pool:
        logger.error("Ace pool not initialized.")
        return jsonify({"error": "Ace pool not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    pool_list = ace_pool.get_instances_nice()
    pool_list_serialized = [entry.model_dump() for entry in pool_list]

    response = jsonify(pool_list_serialized)
    response.status_code = HTTPStatus.OK
    return response

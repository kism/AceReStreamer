"""Main Stream Site Blueprint."""

from http import HTTPStatus
from pathlib import Path

import requests
from flask import Blueprint, Response, jsonify, redirect, render_template
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_bp import get_ip_from_request, is_ip_allowed
from .authentication_helpers import assumed_auth_failure
from .flask_helpers import get_current_app
from .html_snippets import get_header_snippet
from .logger import get_logger
from .scraper import AceScraper
from .scraper_helpers import get_streams_as_iptv

logger = get_logger(__name__)  # Create a logger: acerestreamer.this_module_name, inherit config from root logger

bp = Blueprint("acerestreamer_scraper", __name__)
ace_scraper: AceScraper | None = None
current_app = get_current_app()

REVERSE_PROXY_EXCLUDED_HEADERS = ["content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive"]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas


def start_scraper() -> None:
    """Method to 'configure' this module. Needs to be called under `with app.app_context():` from __init__.py."""
    global ace_scraper  # noqa: PLW0603 Necessary evil as far as I can tell, could move to all objects but eh...
    scraper_cache = Path(current_app.instance_path) / "ace_quality_cache.json"
    ace_scraper = AceScraper(current_app.aw_conf.scraper, scraper_cache)


@bp.route("/")
def home() -> Response | WerkzeugResponse:
    """Render the home page, redirect to stream if IP is allowed."""
    ip_is_allowed = is_ip_allowed(get_ip_from_request())
    if ip_is_allowed:
        return redirect("/stream")

    return redirect("/login")


@bp.route("/stream")
def webplayer_stream() -> Response | WerkzeugResponse:
    """Render the webpage for a stream."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return Response(
        render_template(
            "stream.html.j2",
            rendered_header=get_header_snippet("Ace ReStreamer"),
        ),
        HTTPStatus.OK,
    )


@bp.route("/iptv")
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
    )


@bp.route("/hls/<path:path>")
def hls_stream(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the HLS from Ace."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if not ace_scraper:
        logger.error("Scraper object not initialized.")
        return jsonify({"error": "Scraper not initialized"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    url = f"{current_app.aw_conf.app.ace_address}/ace/manifest.m3u8?content_id={path}"

    logger.debug("HLS stream requested for path: %s", path)

    try:
        resp = requests.get(url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
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

    # Replace the base URL in the stream with the new address
    # The docker container for acestream will always be localhost:6878
    content_str = content_str.replace("http://localhost:6878", current_app.config["SERVER_NAME"])

    ace_scraper.increment_quality(path, 1)

    return Response(content_str, resp.status_code, headers)


@bp.route("/ace/c/<path:path>")
def ace_content(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the Ace content."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    url = f"{current_app.aw_conf.app.ace_address}/ace/c/{path}"

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

    return Response(resp.content, resp.status_code, headers)


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

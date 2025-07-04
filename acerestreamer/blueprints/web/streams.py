"""Main Stream Site Blueprint."""

from http import HTTPStatus
from pathlib import Path

import requests
from flask import Blueprint, Response, jsonify, redirect, render_template, send_file
from flask_caching import CachedResponse
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_pool, ace_scraper, ip_allow_list
from acerestreamer.services.authentication.helpers import assumed_auth_failure, get_ip_from_request
from acerestreamer.utils import get_header_snippet, replace_m3u_sources
from acerestreamer.utils.flask_helpers import DEFAULT_CACHE_DURATION, cache, get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()
logger = get_logger(__name__)
bp = Blueprint("acerestreamer_scraper", __name__)

REVERSE_PROXY_EXCLUDED_HEADERS = ["content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive"]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas


# region /
@bp.route("/")
def home() -> Response | WerkzeugResponse:
    """Render the home page, redirect to stream if IP is allowed."""
    ip_is_allowed = ip_allow_list.check(get_ip_from_request())
    if ip_is_allowed:
        return redirect("/stream")

    return redirect("/login")


# region /stream
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


# region /hls
@bp.route("/hls/<path:path>")
def hls_stream(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the HLS from Ace."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    instance_ace_hls_m3u8_url = ace_pool.get_instance(path)

    if not instance_ace_hls_m3u8_url:
        msg = f"Can't server hls_stream, Ace pool is full: {path}"
        logger.error("HLS stream error: %s", msg)
        return jsonify({"error": msg}, HTTPStatus.SERVICE_UNAVAILABLE)

    logger.trace("HLS stream requested for path: %s", instance_ace_hls_m3u8_url)

    try:
        resp = requests.get(instance_ace_hls_m3u8_url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
        resp.raise_for_status()
    except requests.Timeout as e:
        error_short = type(e).__name__
        logger.error("reverse proxy timeout /hls/ %s", error_short)  # noqa: TRY400 Too verbose otherwise
        ace_scraper.increment_quality(path, "")
        return jsonify({"error": "HLS stream timeout"}, HTTPStatus.REQUEST_TIMEOUT)
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("reverse proxy failure /hls/ %s %s %s", error_short, e.errno, e.strerror)  # noqa: TRY400 Naa this should be shorter
        ace_scraper.increment_quality(path, "")
        return jsonify({"error": "Failed to fetch HLS stream"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    content_str = resp.content.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS stream received for path: %s", path)
        logger.debug("Content received: %s", content_str[:1000])
        ace_scraper.increment_quality(path, "")
        return jsonify({"error": "Invalid HLS stream", "m3u8": content_str}, HTTPStatus.BAD_REQUEST)

    content_str = replace_m3u_sources(
        m3u_content=content_str,
        ace_address=current_app.are_conf.app.ace_address,
        server_name=current_app.are_conf.flask.SERVER_NAME,
    )

    ace_scraper.increment_quality(path, m3u_playlist=content_str)

    return Response(content_str, resp.status_code, headers)


# region /ace/c/
@bp.route("/ace/c/<path:path>")
def ace_content(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the Ace content."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    url = f"{current_app.are_conf.app.ace_address}/ace/c/{path}"

    logger.trace("Ace content requested for url: %s", url)

    try:
        resp = requests.get(url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("/ace/c/ reverse proxy failure %s", error_short)  # noqa: TRY400 Naa this should be shorter
        return jsonify({"error": "Failed to fetch HLS stream"}, HTTPStatus.INTERNAL_SERVER_ERROR)
    except requests.Timeout as e:
        error_short = type(e).__name__
        logger.error("/ace/c/ reverse proxy timeout %s %s %s", error_short, e.errno, e.strerror)  # noqa: TRY400 Too verbose otherwise
        return jsonify({"error": "Ace content timeout"}, HTTPStatus.REQUEST_TIMEOUT)

    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    response = Response(resp.content, resp.status_code, headers)

    response.headers["Content-Type"] = "video/MP2T"  # Doesn't seem to be necessary

    return response


@bp.route("/tvg-logo/<path:path>")
def tvg_logo(path: str) -> Response | WerkzeugResponse:
    """Serve the TVG logo from the local filesystem."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if current_app.static_folder is None:
        response = jsonify({"error": "Static folder not configured"})
        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return response

    logo_path = Path(current_app.instance_path) / "tvg_logos" / path

    if not logo_path.is_file():
        response = send_file(
            Path(current_app.static_folder) / "default_tvg_logo.png",
        )
        response.headers["Cache-Control"] = "public, max-age=3600"
        response.headers["Content-Type"] = "image/png"
        response.status_code = HTTPStatus.OK
        return response

    response = send_file(
        logo_path,
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response

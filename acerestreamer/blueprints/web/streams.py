"""Stream Handling Blueprint."""

from http import HTTPStatus
from pathlib import Path

import requests
from flask import Blueprint, Response, jsonify, request, send_file
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_pool, ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils import check_valid_content_id_or_infohash, replace_hls_m3u_sources
from acerestreamer.utils.flask_helpers import get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()
logger = get_logger(__name__)
bp = Blueprint("acerestreamer_stream", __name__)

REVERSE_PROXY_EXCLUDED_HEADERS = ["content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive"]
REVERSE_PROXY_TIMEOUT = 10  # Very high but alas


# region /hls/
@bp.route("/hls/<path>")
def hls_stream(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the HLS from Ace."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if not check_valid_content_id_or_infohash(path):
        msg = f"Invalid content ID or infohash: {path}"
        logger.error("HLS stream error: %s", msg)
        response = jsonify({"error": msg})
        response.status_code = HTTPStatus.BAD_REQUEST
        return response

    instance_ace_hls_m3u8_url = ace_pool.get_instance_hls_url_by_content_id(path)

    if not instance_ace_hls_m3u8_url:
        msg = f"Can't serve hls_stream, Ace pool is full: {path}"
        logger.error("HLS stream error: %s", msg)
        response = jsonify({"error": msg})
        response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        return response

    logger.trace("HLS stream requested for path: %s", instance_ace_hls_m3u8_url)

    try:
        ace_resp = requests.get(instance_ace_hls_m3u8_url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
        ace_resp.raise_for_status()
    except requests.RequestException as e:
        error_short = type(e).__name__

        # Determine error type and response
        if isinstance(e, requests.Timeout):
            logger.error("reverse proxy timeout /hls/ %s", error_short)  # noqa: TRY400 Short error for requests
            error_msg, status = "HLS stream timeout", HTTPStatus.REQUEST_TIMEOUT
            ace_scraper.increment_quality(path, "")
        elif isinstance(e, requests.ConnectionError):
            logger.error("%s reverse proxy cannot connect to Ace", error_short)  # noqa: TRY400 Short error for requests
            error_msg, status = "Cannot connect to Ace", HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            logger.error("reverse proxy failure /hls/ %s", error_short)  # noqa: TRY400 Short error for requests
            error_msg, status = "Failed to fetch HLS stream", HTTPStatus.INTERNAL_SERVER_ERROR
            ace_scraper.increment_quality(path, "")

        response = jsonify({"error": error_msg})
        response.status_code = status
        return response

    headers = [
        (name, value)
        for (name, value) in ace_resp.raw.headers.items()
        if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    content_str = ace_resp.content.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS stream received for path: %s", path)
        logger.debug("Content received: %s", content_str[:1000])
        ace_scraper.increment_quality(path, "")
        response = jsonify({"error": "Invalid HLS stream", "m3u8": content_str})
        response.status_code = HTTPStatus.BAD_REQUEST
        return response

    content_str = replace_hls_m3u_sources(
        m3u_content=content_str,
        ace_address=current_app.are_conf.app.ace_address,
        server_name=current_app.are_conf.flask.SERVER_NAME,
    )

    ace_scraper.increment_quality(path, m3u_playlist=content_str)

    return Response(content_str, ace_resp.status_code, headers)


# region /hls/m/
# Taking the easy route and capturing the full following path
@bp.route("/hls/m/<path:path>")
def hls_multistream(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the HLS multistream from Ace."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    content_id = ace_pool.get_instance_by_multistream_path(path)

    url = f"{current_app.are_conf.app.ace_address}/hls/m/{path}"

    try:
        ace_resp = requests.get(url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
        ace_resp.raise_for_status()
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("reverse proxy failure /hls/m/ %s", error_short)  # noqa: TRY400 Short error for requests
        error_msg = "Failed to fetch HLS multistream"

        response = jsonify({"error": error_msg})
        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return response

    content_str = ace_resp.content.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS stream received for path: %s", path)
        logger.debug("Content received: %s", content_str[:1000])
        ace_scraper.increment_quality(content_id, "")
        response = jsonify({"error": "Invalid HLS stream", "m3u8": content_str})
        response.status_code = HTTPStatus.BAD_REQUEST
        return response

    content_str = replace_hls_m3u_sources(
        m3u_content=content_str,
        ace_address=current_app.are_conf.app.ace_address,
        server_name=current_app.are_conf.flask.SERVER_NAME,
    )

    ace_scraper.increment_quality(content_id, m3u_playlist=content_str)

    return Response(content_str, ace_resp.status_code)


# region XC
# Depending on the Client, it will either be:
# /a/a/<xc_id>            | Smarters Player Lite (iOS), iMPlayer Android
# /live/a/a/<xc_id>.m3u8  | UHF, M3UAndroid
# /live/a/a/<xc_id>.ts    | iMPlayer iOS, TiViMate, Purple Simple (okay that m3u8 is the response)
# /live/a/a/<tvg_id>.m3u8 | SparkleTV
# One time UHF requested /a/b/ which I don't understand.
@bp.route("/live/a/<_thing2>/<path>")
@bp.route("/a/<_thing2>/<path>")
def xc_m3u8(_thing2: str, path: str) -> Response | WerkzeugResponse:
    """Serve the XC m3u8 file for Ace content."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    content_id: str | None = None

    logger.debug(
        "XC HLS: path='%s' args='%s' ua='%s'",
        request.path,
        ",".join(request.args.values()),
        request.headers.get("User-Agent", ""),
    )

    try:
        xc_id_clean = path.split(".")[0]  # Remove file extension if present, we actually don't care which one
    except IndexError:
        xc_id_clean = path

    try:
        xc_id_int = int(xc_id_clean)
        content_id = ace_scraper.get_content_id_by_xc_id(xc_id_int)
    except ValueError:
        if path.endswith(".m3u8"):
            path = path.replace(".m3u8", "")
        elif path.endswith(".m3u"):
            path = path.replace(".m3u", "")

        content_id = ace_scraper.get_content_id_by_tvg_id(path)

    if content_id is None:
        response = jsonify({"error": "Invalid XC ID format"})
        response.status_code = HTTPStatus.BAD_REQUEST
        return response

    if not content_id:
        response = jsonify({"error": "Content ID not found for the given XC ID"})
        response.status_code = HTTPStatus.NOT_FOUND
        return response

    return hls_stream(content_id)


# region /ace/c/ and /hls/c/ Content paths for regular and multistream
# Do a full path capture here, since ace puts a bunch of stuff following
@bp.route("/ace/c/<path:path>")
@bp.route("/hls/c/<path:path>")
def ace_content(path: str) -> Response | WerkzeugResponse:
    """Reverse proxy the Ace content."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    # Determine the correct URL based on the request path
    if "/hls/c/" in request.path:
        url = f"{current_app.are_conf.app.ace_address}/hls/c/{path}"
        route_prefix = "/hls/c/"
    else:
        url = f"{current_app.are_conf.app.ace_address}/ace/c/{path}"
        route_prefix = "/ace/c/"

    logger.trace("Ace content requested for url: %s", url)

    try:
        resp = requests.get(url, timeout=REVERSE_PROXY_TIMEOUT, stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("%s reverse proxy failure %s", route_prefix, error_short)  # noqa: TRY400 Short error for requests
        response = jsonify({"error": "Failed to fetch HLS stream"})
        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return response
    except requests.Timeout as e:
        error_short = type(e).__name__
        logger.error("%s reverse proxy timeout %s %s %s", route_prefix, error_short, e.errno, e.strerror)  # noqa: TRY400 Short error for requests
        response = jsonify({"error": "Ace content timeout"})
        response.status_code = HTTPStatus.REQUEST_TIMEOUT
        return response

    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in REVERSE_PROXY_EXCLUDED_HEADERS
    ]

    response = Response(resp.content, resp.status_code, headers)

    response.headers["Content-Type"] = "video/MP2T"  # Doesn't seem to be necessary, Apple says so in the spec

    return response


# region /tvg-logo/
@bp.route("/tvg-logo/<path>")
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

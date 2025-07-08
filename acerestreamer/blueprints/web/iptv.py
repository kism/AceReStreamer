"""Blueprint for IPTV functionality in Ace Streamer."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils import xc
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_iptv", __name__)


# region /iptv
@bp.route("/iptv")
@bp.route("/iptv.m3u")
@bp.route("/iptv.m3u8")
def iptv() -> Response | WerkzeugResponse:
    """Render the IPTV page."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    m3u8 = ace_scraper.get_streams_as_iptv()

    return Response(
        m3u8,
        HTTPStatus.OK,
        mimetype="application/vnd.apple.mpegurl",
    )


# region xc
@bp.route("/get.php")
def xc_get() -> Response | WerkzeugResponse:
    """Emulate an XC /get.php endpoint."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if request.args.get("type") == "m3u_plus":
        m3u8 = ace_scraper.get_streams_as_iptv()
        return Response(
            m3u8,
            HTTPStatus.OK,
            mimetype="application/vnd.apple.mpegurl",
        )

    response = jsonify({"error": "Invalid request type. Expected 'type=m3u_plus'."})
    response.status_code = HTTPStatus.BAD_REQUEST
    return response


@bp.route("/player_api.php")
def xc_iptv() -> Response | WerkzeugResponse:
    """Emulate an XC /player_api.php endpoint."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if request.args.get("action") == "get_live_categories":
        xc_resp = jsonify([xc.XCCategory().model_dump()])
    elif request.args.get("action") == "get_live_streams":
        streams = [stream.model_dump() for stream in ace_scraper.get_streams_as_iptv_xc()]
        xc_resp = jsonify(streams)
    elif (
        request.args.get("action") == "get_vod_categories"
        or request.args.get("action") == "get_vod_streams"
        or request.args.get("action") == "get_series_categories"
        or request.args.get("action") == "get_series"
    ):
        xc_resp = jsonify([])
    elif request.args.get("action", None):
        logger.warning("Unknown action '%s' in /player_api.php", request.args.get("action"))
        xc_resp = jsonify([])
    else:
        xc_server_info = xc.XCServerInfo(
            url=ace_scraper.external_url,
        )
        xc_resp = Response(
            xc.XCApiResponse(server_info=xc_server_info).model_dump_json(), HTTPStatus.OK, mimetype="application/json"
        )

    xc_resp.status_code = HTTPStatus.OK
    return xc_resp

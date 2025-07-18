"""Blueprint for IPTV functionality in Ace Streamer."""

from datetime import UTC, datetime
from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.instances_mapping import category_xc_category_id_mapping
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.services.xc import helpers as xc_helpers
from acerestreamer.services.xc import models as xc_models
from acerestreamer.utils import log_unexpected_args
from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_api_xc", __name__)


# region XC
# Due to circular imports, this is here
def _populate_xc_api_response(external_url: str, username: str, password: str) -> xc_models.XCApiResponse:
    """Populate the XC API response with user and server information."""
    http_port, https_port, protocol = xc_helpers.get_port_and_protocol_from_external_url(external_url)

    return xc_models.XCApiResponse(
        user_info=xc_models.XCUserInfo(
            username=username,
            password=password,
            exp_date=xc_helpers.get_expiry_date(),
        ),
        server_info=xc_models.XCServerInfo(
            url=external_url,
            port=http_port,
            https_port=https_port,
            server_protocol=protocol,
            timestamp_now=int(datetime.now(tz=UTC).timestamp()),
            time_now=datetime.now(tz=OUR_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


@bp.route("/player_api.php")
def xc_iptv() -> Response | WerkzeugResponse:
    """Emulate an XC /player_api.php endpoint."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    known_args = ["action", "username", "password", "category_id"]
    log_unexpected_args(
        expected_args=known_args,
        received_args=list(request.args.keys()),
        endpoint="/player_api.php",
    )

    password = request.args.get("password", "")
    username = request.args.get("username", "")

    if request.args.get("action") == "get_live_categories":
        # Get all the categories that are actually in use
        categories_in_use = {stream.category_id for stream in ace_scraper.get_streams_as_iptv_xc(None)}
        # Convert them to integers because the XC 'spec' says they should be strings, despite being numeric
        categories_in_use_int = {int(cat_id) for cat_id in categories_in_use if cat_id.isdigit()}
        # Get a list of XCCategory objects
        categories = category_xc_category_id_mapping.get_all_categories_api(categories_in_use_int)
        # Jsonify
        xc_resp = jsonify([category.model_dump() for category in categories])
    elif request.args.get("action") == "get_live_streams":
        category_id = request.args.get("category_id", "")
        xc_category = int(category_id) if category_id.isdigit() else None
        streams = [stream.model_dump() for stream in ace_scraper.get_streams_as_iptv_xc(xc_category)]
        xc_resp = jsonify(streams)
    elif (
        request.args.get("action") == "get_vod_categories"
        or request.args.get("action") == "get_vod_streams"
        or request.args.get("action") == "get_series_categories"
        or request.args.get("action") == "get_series"
    ):
        xc_resp = jsonify([])  # We don't support these
    elif request.args.get("action", None):
        logger.warning("Unknown action '%s' in /player_api.php", request.args.get("action"))
        xc_resp = jsonify([])
    else:
        xc_api_response = _populate_xc_api_response(
            external_url=ace_scraper.external_url,
            username=username,
            password=password,
        )

        xc_resp = jsonify(xc_api_response.model_dump())
        xc_resp.status_code = HTTPStatus.OK

    xc_resp.status_code = HTTPStatus.OK
    return xc_resp


@bp.route("/get.php")
def xc_get() -> Response | WerkzeugResponse:
    """Emulate an XC /get.php endpoint."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    known_args = ["type", "output"]
    log_unexpected_args(
        expected_args=known_args,
        received_args=list(request.args.keys()),
        endpoint="/get.php",
    )

    if request.args.get("type") == "m3u_plus":
        m3u8 = ace_scraper.get_streams_as_iptv()
        return Response(
            m3u8,
            HTTPStatus.OK,
            mimetype="application/vnd.apple.mpegurl",
        )

    response = jsonify({"error": "Invalid request type, Expected 'type=m3u_plus'"})
    response.status_code = HTTPStatus.BAD_REQUEST
    return response

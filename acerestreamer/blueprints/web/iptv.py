"""Blueprint for IPTV functionality in Ace Streamer."""

from http import HTTPStatus

from flask import Blueprint, Response
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.flask_helpers import get_current_app

current_app = get_current_app()

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

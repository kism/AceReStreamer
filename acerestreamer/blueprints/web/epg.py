"""Blueprint for EPG Endpoints."""

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure

bp = Blueprint("acerestreamer_epg", __name__)

epg_handler = ace_scraper.epg_handler


@bp.route("/epg", methods=["GET"])
@bp.route("/epg.xml", methods=["GET"])
@bp.route("/xmltv", methods=["GET"])
@bp.route("/xmltv.php", methods=["GET"])
def get_epg() -> Response | WerkzeugResponse:
    """Get the merged EPG data."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    condensed_epg = epg_handler.get_condensed_epg()

    response = Response(condensed_epg, mimetype="application/xml")
    response.headers["Content-Disposition"] = 'attachment; filename="condensed_epg.xml"'
    return response

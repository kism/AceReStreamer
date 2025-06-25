"""Blueprint for EPG Endpoints."""

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_helpers import assumed_auth_failure
from .epg import EPGHandler
from .flask_helpers import get_current_app

current_app = get_current_app()

bp = Blueprint("acerestreamer_epg", __name__)

epg_handler = EPGHandler()


@bp.route("/api/epgs", methods=["GET"])
def get_epgs() -> Response | WerkzeugResponse:
    """Get the list of EPGs."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return jsonify(epg_handler.get_epg_names())


@bp.route("/epg", methods=["GET"])
@bp.route("/epg.xml", methods=["GET"])
@bp.route("/xmltv", methods=["GET"])
@bp.route("/xmltv.php", methods=["GET"])
def get_epg() -> Response | WerkzeugResponse:
    """Get the merged EPG data."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    merged_epg = epg_handler.get_merged_epg()

    response = Response(merged_epg, mimetype="application/xml")
    response.headers["Content-Disposition"] = 'attachment; filename="merged_epg.xml"'
    return response

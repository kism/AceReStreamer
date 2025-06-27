"""Blueprint for EPG Endpoints."""

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure

bp = Blueprint("acerestreamer_epg", __name__)

epg_handler = ace_scraper.epg_handler

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

    condensed_epg = epg_handler.get_condensed_epg()

    response = Response(condensed_epg, mimetype="application/xml")
    response.headers["Content-Disposition"] = 'attachment; filename="condensed_epg.xml"'
    return response


@bp.route("/epg_full", methods=["GET"])
@bp.route("/epg_full.xml", methods=["GET"])
def get_full_epg() -> Response | WerkzeugResponse:
    """Get the full EPG data."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    get_merged_epg = epg_handler.get_merged_epg()

    response = Response(get_merged_epg, mimetype="application/xml")
    response.headers["Content-Disposition"] = 'attachment; filename="full_epg.xml"'
    return response

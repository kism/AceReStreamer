"""Blueprint for EPG Endpoints."""

from pathlib import Path

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_helpers import assumed_auth_failure
from .epg import EPGHandler
from .flask_helpers import get_current_app

current_app = get_current_app()

bp = Blueprint("acerestreamer_epg", __name__)

epg_handler = EPGHandler(epg_conf_list=[])


def start_epg_handler() -> None:
    """Start the EPG handler with the provided URLs."""
    global epg_handler  # noqa: PLW0603 Hard to avoid
    instance_path = Path(current_app.instance_path)
    epg_handler = EPGHandler(epg_conf_list=current_app.aw_conf.epgs, instance_path=instance_path)


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

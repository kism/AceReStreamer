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

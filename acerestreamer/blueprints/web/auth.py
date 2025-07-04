"""Main Stream Site Blueprint."""

from flask import Blueprint, Response, send_file
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.utils.constants import STATIC_DIRECTORY
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

# Register this module (__name__) as available to the blueprints of acerestreamer, I think https://flask.palletsprojects.com/en/3.0.x/blueprints/
bp = Blueprint("acerestreamer_auth", __name__)


@bp.route("/login")
def login() -> Response | WerkzeugResponse:
    """Render the login page."""
    return send_file(STATIC_DIRECTORY / "login.html")

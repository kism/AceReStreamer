"""Main Stream Site Blueprint."""

import hmac
from http import HTTPStatus

from flask import Blueprint, Response, jsonify, redirect, request
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ip_allow_list
from acerestreamer.services.authentication import get_ip_from_request, is_ip_allowed
from acerestreamer.utils.flask_helpers import get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_api_auth", __name__)


@bp.route("/api/authenticate", methods=["GET", "POST"])
def authenticate() -> Response | WerkzeugResponse:
    """Authenticate the user."""
    if request.method == "POST":
        password = request.form.get("password", "").strip()

        # This authentication is so cooked, but by doing this I avoid a string compare / timing attacks
        if hmac.compare_digest(
            current_app.aw_conf.app.password,
            password,
        ):
            ip = get_ip_from_request()
            if ip != "":
                ip_allow_list.add(ip)
                logger.info("Authenticated IP address: %s", ip)
            else:
                logger.warning("Failed to get IP address from request, authentication may not be secure.")
                response = jsonify({"status": "error", "message": "Failed to get IP address from request"})
                response.status_code = HTTPStatus.BAD_REQUEST
                return response

            return redirect(
                f"{current_app.aw_conf.flask.SERVER_NAME}/stream",
                code=HTTPStatus.FOUND,
            )

        response = jsonify({"status": "error", "message": "Authentication failed"})
        response.status_code = HTTPStatus.UNAUTHORIZED

    # Get the current authentication
    if request.method == "GET":
        ip = get_ip_from_request()
        if not is_ip_allowed(ip):
            response = jsonify({"status": "error", "message": "Unauthenticated"})
            response.status_code = HTTPStatus.UNAUTHORIZED
            return response

        response = jsonify({"status": "success", "message": "Authenticated successfully"})

    return response

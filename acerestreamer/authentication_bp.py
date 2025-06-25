"""Main Stream Site Blueprint."""

import hmac
from http import HTTPStatus
from pathlib import Path

from flask import Blueprint, Response, jsonify, redirect, request, send_file
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_allow_list import AllowList
from .flask_helpers import aw_conf
from .logger import get_logger

logger = get_logger(__name__)  # Create a logger: acerestreamer.this_module_name, inherit config from root logger

# Register this module (__name__) as available to the blueprints of acerestreamer, I think https://flask.palletsprojects.com/en/3.0.x/blueprints/
bp = Blueprint("acerestreamer_auth", __name__)

ip_allow_list: AllowList = AllowList()

STATIC_PATH = Path(__file__).parent / "static"


def get_ip_from_request() -> str:
    """Get the IP address from the request."""
    request_ip_raw = (
        request.environ.get("HTTP_X_FORWARDED_FOR")
        or request.environ.get("HTTP_X_REAL_IP")
        or request.environ.get("REMOTE_ADDR")
        or ""
    )

    logger.trace("Raw request IP: %s", request_ip_raw)

    if isinstance(request_ip_raw, list):
        request_ip_raw = request_ip_raw[0]

    if isinstance(request_ip_raw, str):
        return request_ip_raw.strip()

    return str(request_ip_raw).strip()


def is_ip_allowed(ip: str) -> bool:
    """Check if the IP address is allowed."""
    logger.trace("Checking if IP is allowed: %s", ip)
    return ip_allow_list.check(ip)


@bp.route("/api/authenticate", methods=["GET", "POST"])
def authenticate() -> Response | WerkzeugResponse:
    """Authenticate the user."""
    if request.method == "POST":
        password = request.form.get("password", "").strip()

        # This authentication is so cooked, but by doing this I avoid a string compare / timing attacks
        if hmac.compare_digest(
            aw_conf.app.password,
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
                f"{aw_conf.flask.SERVER_NAME}/stream",
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


@bp.route("/login")
def login() -> Response | WerkzeugResponse:
    """Render the login page."""
    return send_file(STATIC_PATH / "login.html")

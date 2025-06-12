"""Main Stream Site Blueprint."""

import hmac
from http import HTTPStatus
from pathlib import Path

from flask import Blueprint, Response, jsonify, redirect, request
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_allow_list import AllowList
from .flask_helpers import get_current_app
from .logger import get_logger

logger = get_logger(__name__)  # Create a logger: acestreamwebplayer.this_module_name, inherit config from root logger

# Register this module (__name__) as available to the blueprints of acestreamwebplayer, I think https://flask.palletsprojects.com/en/3.0.x/blueprints/
bp = Blueprint("acestreamwebplayer_auth", __name__)

current_app = get_current_app()
ip_allow_list: None | AllowList = None


def start_allowlist() -> None:
    """Initialize the allow list from the configuration."""
    global ip_allow_list  # noqa: PLW0603
    allowlist_path = Path(current_app.instance_path) / "allowed_ips.json"
    nginx_allowlist_path = Path(current_app.aw_conf.nginx.ip_allow_list_path) if current_app.aw_conf.nginx else None
    ip_allow_list = AllowList(allowlist_path, nginx_allowlist_path)


def get_ip_from_request() -> str:
    """Get the IP address from the request."""
    request_ip_raw = (
        request.environ.get("HTTP_X_FORWARDED_FOR")
        or request.environ.get("HTTP_X_REAL_IP")
        or request.environ.get("REMOTE_ADDR")
        or ""
    )

    logger.debug("Raw request IP: %s", request_ip_raw)

    if isinstance(request_ip_raw, list):
        request_ip_raw = request_ip_raw[0]

    if isinstance(request_ip_raw, str):
        return request_ip_raw.strip()

    return str(request_ip_raw).strip()


def is_ip_allowed(ip: str) -> bool:
    """Check if the IP address is allowed."""
    if not ip_allow_list:
        logger.warning("IP_ALLOW_LIST is not initialized")
        return False

    logger.debug("Checking if IP is allowed: %s", ip)
    return ip_allow_list.check(ip)


@bp.route("/api/authenticate", methods=["GET", "POST"])
def authenticate() -> Response | WerkzeugResponse:
    """Authenticate the user."""
    if not ip_allow_list:
        return Response("Not initialized", HTTPStatus.INTERNAL_SERVER_ERROR)

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
            response = jsonify({"status": "error", "message": "IP address not allowed"})
            response.status_code = HTTPStatus.FORBIDDEN
            return response

        response = jsonify({"status": "success", "message": "Authenticated successfully"})

    return response

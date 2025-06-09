"""Main Stream Site Blueprint."""

import json
from pathlib import Path
from http import HTTPStatus

from flask import Blueprint, Response, jsonify, redirect, request
from werkzeug.wrappers import Response as WerkzeugResponse

from .flask_helpers import get_current_app
from .logger import get_logger

# Modules should all setup logging like this so the log messages include the modules name.
# If you were to list all loggers with something like...
# `loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]`
# Before creating this object, you would not see a logger with this modules name (acestreamwebplayer.this_module_name)
logger = get_logger(__name__)  # Create a logger: acestreamwebplayer.this_module_name, inherit config from root logger

# Register this module (__name__) as available to the blueprints of acestreamwebplayer, I think https://flask.palletsprojects.com/en/3.0.x/blueprints/
bp = Blueprint("acestreamwebplayer_auth", __name__)

current_app = get_current_app()


class AllowList:
    """A simple allow list for IP addresses."""

    def __init__(self, allowlist_path: Path | None) -> None:
        """Initialize the allow list with a path to the allow list file."""
        self.allowlist_path = allowlist_path
        self.allowlist_ips: list[str] = []
        self.load()

    def add(self, ip: str) -> None:
        """Add an IP address to the allow list."""
        if ip == "":
            logger.warning("Attempted to add an empty IP address to the allow list.")
            return

        if ip not in self.allowlist_ips:
            self.allowlist_ips.append(ip)
            logger.info("Added IP address to allow list: %s", ip)
            self.save()

    def check(self, ip: str) -> bool:
        """Check if an IP address is in the allow list."""
        return ip in self.allowlist_ips

    def load(self) -> None:
        """Load the allow list from a file."""
        if not self.allowlist_path:
            return

        if self.allowlist_path.exists():
            with self.allowlist_path.open("r") as f:
                self.allowlist_ips = json.load(f)

    def save(self) -> None:
        """Save the allow list to a file."""
        if not self.allowlist_path:
            return

        with self.allowlist_path.open("w") as f:
            json.dump(self.allowlist_ips, f)


IP_ALLOW_LIST: None | AllowList = None


def start_allowlist() -> None:
    """Initialize the allow list from the configuration."""
    global IP_ALLOW_LIST  # noqa: PLW0603
    allowlist_path = Path(current_app.instance_path) / "allowed_ips.json"
    IP_ALLOW_LIST = AllowList(allowlist_path)


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
    if not IP_ALLOW_LIST:
        logger.warning("IP_ALLOW_LIST is not initialized")
        return False

    logger.debug("Checking if IP is allowed: %s", ip)
    return IP_ALLOW_LIST.check(ip)


@bp.route("/api/authenticate")
@bp.route("/api/authenticate/")
@bp.route("/api/authenticate/<password>")
def authenticate(password: str = "") -> Response | WerkzeugResponse:
    """Authenticate the user."""
    if not IP_ALLOW_LIST:
        return Response("Not initialized", HTTPStatus.INTERNAL_SERVER_ERROR)

    if password == current_app.aw_conf.app.password:
        ip = get_ip_from_request()
        if ip != "":
            IP_ALLOW_LIST.add(ip)
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

    return response

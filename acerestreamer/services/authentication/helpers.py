"""Authentication helpers."""

from http import HTTPStatus

from flask import Response, abort, request

from acerestreamer.utils.flask_helpers import STATIC_DIRECTORY, get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()

logger = get_logger(__name__)  # Create a logger: acerestreamer.authentication_helpers, inherit config from root logger


def assumed_auth_failure() -> None | Response:
    """Check if the IP is allowed."""
    if not current_app.aw_conf.app.password:
        return None

    if is_ip_allowed(get_ip_from_request()):
        return None

    file = STATIC_DIRECTORY / "401.html"
    if not file.exists():
        logger.error("The 401.html file does not exist in the static folder: %s", file)

    abort(HTTPStatus.UNAUTHORIZED, description="Unauthorized access")


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
    from acerestreamer.instances import ip_allow_list
    logger.trace("Checking if IP is allowed: %s", ip)
    return ip_allow_list.check(ip)

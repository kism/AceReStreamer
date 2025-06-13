"""Authentication helpers."""

from http import HTTPStatus

from flask import Response, abort

from .authentication_bp import get_ip_from_request, is_ip_allowed
from .flask_helpers import STATIC_DIRECTORY, get_current_app
from .logger import get_logger

logger = get_logger(__name__)  # Create a logger: acerestreamer.authentication_helpers, inherit config from root logger

current_app = get_current_app()


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

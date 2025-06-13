"""Authentication helpers."""

from http import HTTPStatus

from flask import Response, redirect
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_bp import get_ip_from_request, is_ip_allowed
from .flask_helpers import get_current_app

current_app = get_current_app()


def assumed_auth_failure() -> None | Response | WerkzeugResponse:
    """Check if the IP is allowed."""
    if not current_app.aw_conf.app.password:
        return None

    if is_ip_allowed(get_ip_from_request()):
        return None

    return redirect("/", HTTPStatus.UNAUTHORIZED)

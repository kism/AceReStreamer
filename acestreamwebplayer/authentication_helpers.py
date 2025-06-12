"""Authentication helpers."""

from http import HTTPStatus

from flask import Response, redirect
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_bp import get_ip_from_request, is_ip_allowed


def assumed_auth_failure() -> None | Response | WerkzeugResponse:
    """Check if the IP is allowed."""
    if is_ip_allowed(get_ip_from_request()):
        return None

    return redirect("/", HTTPStatus.UNAUTHORIZED)

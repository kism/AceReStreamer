"""Home Web Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, redirect, render_template
from flask_caching import CachedResponse
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ip_allow_list
from acerestreamer.services.authentication.helpers import assumed_auth_failure, get_ip_from_request
from acerestreamer.utils import get_header_snippet
from acerestreamer.utils.flask_helpers import DEFAULT_CACHE_DURATION, cache, get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()
logger = get_logger(__name__)
bp = Blueprint("acerestreamer_home", __name__)


# region /
@bp.route("/")
def home() -> Response | WerkzeugResponse:
    """Render the home page, redirect to stream if IP is allowed."""
    ip_is_allowed = ip_allow_list.check(get_ip_from_request())
    if ip_is_allowed:
        return redirect("/stream")

    return redirect("/login")


# region /stream
@bp.route("/stream")
@cache.cached()
def webplayer_stream() -> Response | WerkzeugResponse | CachedResponse:
    """Render the webpage for a stream."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return CachedResponse(  # type: ignore[no-untyped-call] # Missing from flask-caching
        response=Response(
            render_template(
                "stream.html.j2",
                rendered_header=get_header_snippet("Ace ReStreamer"),
            ),
            HTTPStatus.OK,
        ),
        timeout=DEFAULT_CACHE_DURATION,
    )

"""Blueprints for the info pages."""

from http import HTTPStatus

from flask import Blueprint, Response, render_template
from flask_caching import CachedResponse
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_helpers import assumed_auth_failure
from .flask_helpers import DEFAULT_CACHE_DURATION, aw_conf, cache
from .html_snippets import get_header_snippet
from .logger import get_logger

bp = Blueprint("acerestreamer_info", __name__, template_folder="templates/info")

logger = get_logger(__name__)


@bp.route("/info/guide")
@cache.cached()
def info_guide() -> Response | WerkzeugResponse | CachedResponse:
    """Render the guide page."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return CachedResponse(  # type: ignore[no-untyped-call] # Missing from flask-caching
        response=Response(
            render_template(
                "guide.html.j2",
                rendered_header=get_header_snippet("Ace ReStreamer Guide"),
            ),
            status=HTTPStatus.OK,
        ),
        timeout=DEFAULT_CACHE_DURATION,
    )


@bp.route("/info/iptv")
@cache.cached()
def guide() -> Response | WerkzeugResponse:
    """Render the guide page."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return CachedResponse(  # type: ignore[no-untyped-call] # Missing from flask-caching
        response=Response(
            render_template(
                "iptv.html.j2",
                server_base_url=aw_conf.flask.SERVER_NAME,
                rendered_header=get_header_snippet("Ace ReStreamer Guide"),
            ),
            status=HTTPStatus.OK,
        ),
        timeout=DEFAULT_CACHE_DURATION,
    )


@bp.route("/info/api")
@cache.cached()
def api() -> Response | WerkzeugResponse:
    """Render the API information page."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return CachedResponse(  # type: ignore[no-untyped-call] # Missing from flask-caching
        response=Response(
            render_template(
                "api.html.j2",
                rendered_header=get_header_snippet("Ace ReStreamer API Information"),
            ),
            status=HTTPStatus.OK,
        ),
        timeout=DEFAULT_CACHE_DURATION,
    )

"""Blueprints for the info pages."""

from http import HTTPStatus

from flask import Blueprint, Response, render_template
from flask_caching import CachedResponse
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.services.authentication import assumed_auth_failure
from acerestreamer.utils import get_header_snippet
from acerestreamer.utils.flask_helpers import DEFAULT_CACHE_DURATION, cache, get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()

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

    logger.warning(current_app.are_conf.flask.SERVER_NAME)

    return CachedResponse(  # type: ignore[no-untyped-call] # Missing from flask-caching
        response=Response(
            render_template(
                "iptv.html.j2",
                server_base_url=current_app.are_conf.flask.SERVER_NAME,
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

"""Blueprints for the info pages."""

from http import HTTPStatus

from flask import Blueprint, Response, render_template
from werkzeug.wrappers import Response as WerkzeugResponse

from .authentication_helpers import assumed_auth_failure
from .flask_helpers import get_current_app
from .html_snippets import get_header_snippet
from .logger import get_logger

bp = Blueprint("acestreamwebplayer_info", __name__, template_folder="templates/info")
current_app = get_current_app()
logger = get_logger(__name__)


@bp.route("/info/guide")
def info_guide() -> Response | WerkzeugResponse:
    """Render the guide page."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    return Response(
        render_template(
            "guide.html.j2",
            rendered_header=get_header_snippet("Ace ReStreamer Guide"),
        ),
        HTTPStatus.OK,
    )


@bp.route("/info/iptv")
def guide() -> Response | WerkzeugResponse:
    """Render the guide page."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    context = {
        "iptv_main_url": current_app.aw_conf.flask.SERVER_NAME + "/iptv",
        "rendered_header": get_header_snippet("Ace ReStreamer IPTV Guide"),
    }

    logger.warning(context)

    return Response(
        render_template("iptv.html.j2", **context),
        HTTPStatus.OK,
    )

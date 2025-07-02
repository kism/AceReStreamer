"""AcePool API Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_pool
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_acepool_api", __name__)


# region /api/ace_pool
@bp.route("/api/ace_pool")
def api_ace_pool() -> Response | WerkzeugResponse:
    """API endpoint to get the Ace pool."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    pool_list = ace_pool.get_instances_nice()
    pool_list_serialized = pool_list.model_dump()

    response = jsonify(pool_list_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace_pool/<path:ace_content_id>", methods=["GET", "DELETE"])
def api_ace_pool_by_id(ace_content_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get or delete an Ace pool entry by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    instance_url = ace_pool.get_instance(ace_content_id)

    if instance_url is None:
        logger.error("Ace ID %s not found in pool", ace_content_id)
        return jsonify({"error": "Ace ID not found"}, HTTPStatus.NOT_FOUND)

    if request.method == "GET":
        return jsonify({"ace_url": instance_url}, HTTPStatus.OK)

    if request.method == "DELETE":
        ace_pool.remove_instance_by_ace_content_id(
            ace_content_id, caller="API"
        )  # Assume success since we validated above
        return jsonify({"message": "Ace ID removed successfully"}, HTTPStatus.OK)

    return jsonify({"error": "Method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)


@bp.route("/api/ace_pool_stats")
def api_ace_pool_stats() -> Response | WerkzeugResponse:
    """API endpoint to get Ace pool stats."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    ace_pool_stats = ace_pool.get_all_stats()

    response = jsonify(ace_pool_stats)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace_pool_stats/<path:pid_str>")
def api_ace_pool_stats_by_id(pid_str: str) -> Response | WerkzeugResponse:
    """API endpoint to get Ace pool stats by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    try:
        pid_int = int(pid_str)
    except ValueError as e:
        error_short = type(e).__name__
        logger.error("Invalid Ace PID: %s", pid_str)  # noqa: TRY400 Short error please
        return jsonify({"error": "Invalid Ace PID"}, HTTPStatus.BAD_REQUEST)

    ace_pool_stat = ace_pool.get_stats_by_pid(pid_int)

    if ace_pool_stat is None:
        logger.error("Ace ID %s not found in pool stats", error_short)
        return jsonify({"error": "Ace PID not found"}, HTTPStatus.NOT_FOUND)

    response = jsonify(ace_pool_stat.model_dump())
    response.status_code = HTTPStatus.OK
    return response

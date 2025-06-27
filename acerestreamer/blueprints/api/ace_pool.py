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


@bp.route("/api/ace_pool/<path:ace_id>", methods=["GET", "DELETE"])
def api_ace_pool_by_id(ace_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get or delete an Ace pool entry by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    instance_url = ace_pool.get_instance(ace_id)

    if instance_url is None:
        logger.error("Ace ID %s not found in pool", ace_id)
        return jsonify({"error": "Ace ID not found"}, HTTPStatus.NOT_FOUND)

    if request.method == "GET":
        return jsonify({"ace_url": instance_url}, HTTPStatus.OK)

    if request.method == "DELETE":
        ace_pool.remove_instance_by_ace_id(ace_id, caller="API")  # Assume success since we validated above
        return jsonify({"message": "Ace ID removed successfully"}, HTTPStatus.OK)

    return jsonify({"error": "Method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)

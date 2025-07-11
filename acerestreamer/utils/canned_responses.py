"""Common canned flask responses."""

from http import HTTPStatus

from flask import Response, jsonify


def instance_not_found_response(content_id: str, in_what: str) -> Response:
    """Return a response when an Ace instance is not found."""
    msg = f"Ace content_id '{content_id}' not found in {in_what}"

    response = jsonify({"error": msg})
    response.status_code = HTTPStatus.NOT_FOUND
    return response


def pid_not_found_response(pid: str) -> Response:
    """Return a response when an Ace PID is not found."""
    msg = f"Ace PID '{pid}' not found in ace pool"  # PIDs only exist as a concept in the ace pool

    response = jsonify({"error": msg})
    response.status_code = HTTPStatus.NOT_FOUND
    return response

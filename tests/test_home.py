"""Tests the app home page."""

from http import HTTPStatus


def test_home(client):
    """Test the hello API endpoint. This one uses the fixture in conftest.py."""
    response = client.get("/")
    # TEST: HTTP OK
    assert response.status_code == HTTPStatus.OK
    # TEST: Content type
    assert response.content_type == "text/html; charset=utf-8"
    # TEST: It is a webpage that we get back
    assert b"<!doctype html>" in response.data


def test_static_js_exists(client):
    """TEST: /static/acerestreamer.js loads."""
    response = client.get("/static/acerestreamer.js")
    assert response.status_code == HTTPStatus.OK

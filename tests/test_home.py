"""Tests the app home page."""

from http import HTTPStatus

import pytest


def test_home(client):
    """Test the hello API endpoint. This one uses the fixture in conftest.py."""
    response = client.get("/")
    assert response.status_code == HTTPStatus.FOUND


def test_static_js_exists(client):
    """TEST: /static/acestreamwebplayer.js loads."""
    response = client.get("/static/acestreamwebplayer.js")
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "path",
    [
        "/api/streams",
        "/api/sources",
        "/api/streams/health",
        "/api/ace-pool",
        "/api/epgs",
        "/api/health",
    ],
)
def test_api_basic(client, path):
    """Test OK response with no password set."""
    client.post(
        "/api/authenticate",
        data={"password": "testpassword"},
    )

    response = client.get(path)
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "application/json"
    assert b"{" in response.data or b"[" in response.data


def test_misc_endpoints(client):
    """Test some miscellaneous endpoints."""
    client.post(
        "/api/authenticate",
        data={"password": "testpassword"},
    )

    response = client.get("/favicon.ico")
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "image/x-icon"

    response = client.get("/epg")
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "application/xml; charset=utf-8"

    response = client.get("/iptv")
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "application/vnd.apple.mpegurl"

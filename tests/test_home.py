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


@pytest.mark.parametrize("path", ["/login", "/stream", "/info/guide", "/info/iptv", "/info/api"])
def test_login(client, path):
    """Test OK response with no password set."""
    response = client.get(path)
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "text/html; charset=utf-8"
    assert b"<!DOCTYPE html>" in response.data


def test_password(client, app):
    """Test that the password works."""
    app.are_conf.app.password = "testpassword"
    response = client.get("/stream")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    client.post(
        "/api/authenticate",
        data={"password": "testpassword"},
    )
    response = client.get("/stream")
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "path",
    [
        "/api/authenticate",
        "/api/streams/flat",
        "/api/streams/by_source",
        "/api/sources",
        "/api/sources/flat",
        "/api/streams/health",
        "/api/ace_pool",
        "/api/epgs",
    ],
)
def test_api_basic(client, path):
    """Test OK response with no password set."""
    response = client.get(path)
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "application/json"
    assert b"{" in response.data or b"[" in response.data


def test_misc_endpoints(client):
    """Test some miscellaneous endpoints."""
    response = client.get("/favicon.ico")
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "image/x-icon"

    response = client.get("/epg")
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "application/xml; charset=utf-8"

    response = client.get("/iptv")
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "application/vnd.apple.mpegurl"

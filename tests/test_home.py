"""Tests the app home page."""

from http import HTTPStatus

import pytest

from acerestreamer.flask_helpers import aw_conf


def test_home(client):
    """Test the hello API endpoint. This one uses the fixture in conftest.py."""
    response = client.get("/")
    assert response.status_code == HTTPStatus.FOUND


def test_static_js_exists(client):
    """TEST: /static/acestreamwebplayer.js loads."""
    response = client.get("/static/acestreamwebplayer.js")
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("path", ["/login", "/stream"])
def test_login(client, path):
    """Test OK response with no password set."""
    response = client.get(path)
    assert response.status_code == HTTPStatus.OK
    assert response.content_type == "text/html; charset=utf-8"
    assert b"<!DOCTYPE html>" in response.data


def test_password(client, app):
    """Test that the password works."""
    aw_conf.app.password = "testpassword"
    response = client.get("/stream")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    client.post(
        "/api/authenticate",
        data={"password": "testpassword"},
    )
    response = client.get("/stream")
    assert response.status_code == HTTPStatus.OK

"""Tests the blueprint's HTTP endpoint."""

import logging
from http import HTTPStatus

from acestreamwebplayer import create_app


def test_hello(client):
    """TEST: The default /hello/ response, This one uses the fixture in conftest.py."""
    response = client.get("/hello/")
    assert response.status_code == HTTPStatus.OK
    json_data = response.get_json()
    assert json_data["msg"] == "Hello, World!", "Incorrect response from /hello/ when using default config."


def test_hello_with_config(tmp_path, get_test_config, caplog):
    """TEST: the hello API endpoint with non-default config."""
    app = create_app(get_test_config("bp_one_different_my_message.toml"), instance_path=tmp_path)
    client = app.test_client()
    response = client.get("/hello/")
    assert response.status_code == HTTPStatus.OK
    json_data = response.get_json()
    assert json_data["msg"] == "Hello, PyTest!", "Incorrect response from /hello/ when using non-default config."

    expected_log = "GET request to /hello/, returning: {'msg': 'Hello, PyTest!'} as json, due to config: my_message='Hello, PyTest!'"  # noqa: E501 # Its a long log message

    with caplog.at_level(logging.DEBUG):
        assert expected_log in caplog.text


def test_hello_backwards(client):
    """TEST: The default /hello/ response, This one uses the fixture in conftest.py."""
    response = client.get("/hello_backwards/")
    assert response.status_code == HTTPStatus.OK
    json_data = response.get_json()
    assert (
        json_data["msg"] == "!dlroW ,olleH"  # cspell:disable-line
    ), "Incorrect response from /hello_backwards/ when using default config."

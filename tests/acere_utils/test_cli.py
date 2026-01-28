from typing import TYPE_CHECKING

from acere.utils.cli import prompt

if TYPE_CHECKING:
    import pytest
else:
    pytest = object


def test_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the prompt function."""
    test_input = "test user input"
    monkeypatch.setattr("builtins.input", lambda _: test_input)

    response = prompt("Please enter something:")
    assert response == test_input

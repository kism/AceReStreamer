"""Generic API models."""

from pydantic import BaseModel
from pydantic_core import ErrorDetails


class MessageResponseModel(BaseModel):
    """Generic API response message model."""

    message: str
    errors: list[str] | list[ErrorDetails] | None = None

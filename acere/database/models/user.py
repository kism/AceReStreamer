import uuid
from datetime import UTC, datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from acere.utils.auth import generate_stream_token


# Shared properties
class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    stream_token: str = Field(default_factory=generate_stream_token, max_length=64)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("username", mode="before")
    @classmethod
    def username_to_lowercase(cls, v: str) -> str:
        return v.lower()


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    username: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("username", mode="before")
    @classmethod
    def username_to_lowercase(cls, v: str) -> str:
        return v.lower()


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)

    @field_validator("username", mode="before")
    @classmethod
    def username_to_lowercase(cls, v: str | None) -> str | None:  # ty:ignore[invalid-method-override]
        return v.lower() if isinstance(v, str) else v


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)

    @field_validator("username", mode="before")
    @classmethod
    def username_to_lowercase(cls, v: str | None) -> str | None:
        return v.lower() if isinstance(v, str) else v


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    password_changed_at: datetime | None = None

    @field_validator("password_changed_at", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime | None) -> datetime | None:
        """Ensure password_changed_at is timezone-aware (SQLite strips tzinfo)."""
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class StreamToken(SQLModel):
    stream_token: str


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
    iat: int | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

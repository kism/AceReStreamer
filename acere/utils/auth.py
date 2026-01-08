"""Utility functions and helpers."""

from dataclasses import dataclass
from secrets import token_hex

import jwt
from jwt.exceptions import InvalidTokenError

from acere.core import security
from acere.instances.config import settings
from acere.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EmailData:
    html_content: str
    subject: str


# def generate_password_reset_token(email: str) -> str:
#     delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
#     now = datetime.now(timezone.utc)
#     expires = now + delta
#     exp = expires.timestamp()
#     encoded_jwt = jwt.encode(
#         {"exp": exp, "nbf": now, "sub": email},
#         settings.SECRET_KEY,
#         algorithm=security.ALGORITHM,
#     )
#     return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None


def generate_stream_token() -> str:
    return token_hex(5)  # Normal XC things

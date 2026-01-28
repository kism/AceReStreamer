from fastapi import HTTPException
from sqlmodel import Session, select

from acere.database.init import engine
from acere.database.models.user import User
from acere.utils.logger import get_logger

logger = get_logger(__name__)


class StreamTokenManager:
    def __init__(self) -> None:
        self._token_cache: set[str] = set()

    def _update_token_cache(self) -> None:
        """Update the in-memory cache of stream tokens from the database."""
        with Session(engine) as session:
            tokens = session.exec(select(User.stream_token)).all()
            self._token_cache = set(tokens)

    def verify_stream_token(self, token: str) -> bool:
        """Check if the stream token is in the database."""
        in_cache = token in self._token_cache
        if not in_cache:
            self._update_token_cache()

        return token in self._token_cache


_stream_token_manager = StreamTokenManager()


def verify_stream_token(token: str) -> bool:
    """Will raise HTTPException if the stream token is invalid."""
    can_proceed = _stream_token_manager.verify_stream_token(token)

    if not can_proceed:
        logger.trace("Invalid stream token attempted: %s", token)
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing stream token",
        )

    return True

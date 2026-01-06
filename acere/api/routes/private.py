from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from acere.api.deps import SessionDep
from acere.core.security import get_password_hash
from acere.models import (
    User,
    UserPublic,
)
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """
    logger.info(f"Creating user {user_in.username}")

    user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    logger.info(f"User created: {user.username}")

    session.add(user)
    logger.info("Committing to database")
    session.commit()

    logger.info("User committed to database")

    return user

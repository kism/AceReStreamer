from collections.abc import Generator  # noqa: TC003 Will break everything otherwise
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from acere.database.init import engine


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]

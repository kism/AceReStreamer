import secrets

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

from acere import crud
from acere.constants import DATABASE_FILE
from acere.database.models.user import User, UserCreate
from acere.instances.config import settings
from acere.utils.logger import get_logger

logger = get_logger(__name__)
engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    echo=False,
)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def _create_first_superuser(session: Session) -> None:
    user = session.exec(select(User).where(User.username == settings.FIRST_SUPERUSER)).first()
    if not user:
        password_clear = settings.FIRST_SUPERUSER_PASSWORD
        if not password_clear or password_clear.strip() == "":
            password_clear = secrets.token_urlsafe(20)
            msg = f""" Important >>>
-------------------------------------------------------------------------------
The superuser password is not set, generating a random one, this will be printed only once.
Username: {settings.FIRST_SUPERUSER}
Password: {password_clear}
-------------------------------------------------------------------------------"""
            logger.warning(msg)
        else:
            msg = "Setting the superuser password from the environment variable."
            logger.warning(msg)
            settings.FIRST_SUPERUSER_PASSWORD = ""
            settings.write_config()

        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=password_clear,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)


def _migrate_db(session: Session) -> None:
    old_tables = ["acequalitycache", "contentidinfohash", "content_id_infohash", "content_id_xc_id"]
    for table_name in old_tables:
        session.connection().execute(text(f"DROP TABLE IF EXISTS {table_name}"))
    session.commit()


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines

    SQLModel.metadata.create_all(engine)

    _migrate_db(session=session)
    _create_first_superuser(session=session)

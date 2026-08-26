from sqlmodel import SQLModel, create_engine

from acere.database.migration import runner
from acere.instances.paths import get_app_path_handler
from acere.utils.logger import get_logger

logger = get_logger(__name__)
engine = create_engine(
    f"sqlite:///{get_app_path_handler().database_file}",
    echo=False,
)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    runner.upgrade(engine)

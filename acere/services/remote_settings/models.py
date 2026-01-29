from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RemoteSettingsURLSetModel(BaseModel):
    url: HttpUrl | None


class RemoteSettingsURLGetModel(BaseModel):
    url: HttpUrl | None
    status: str
    last_fetched: datetime | None

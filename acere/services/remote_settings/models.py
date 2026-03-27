from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RemoteSettingsSetModel(BaseModel):
    url: HttpUrl | None
    enable_epg: bool = True
    enable_ace: bool = True


class RemoteSettingsGetModel(BaseModel):
    url: HttpUrl | None
    enable_epg: bool
    enable_ace: bool
    status: str
    last_fetched: datetime | None

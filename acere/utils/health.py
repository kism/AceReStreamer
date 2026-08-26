from pydantic import BaseModel


class ThreadHealthModel(BaseModel):
    name: str
    is_alive: bool


class HealthResponseModel(BaseModel):
    version: str
    version_full: str
    time_zone: str
    threads: list[ThreadHealthModel]
    memory_usage_mb: str

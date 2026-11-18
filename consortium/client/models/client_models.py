from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    username: str
    password: str
    remote_host: str
    remote_port: int


class Release(BaseModel):
    version: str
    codename: str  # codenames are reserved for every feature release
    datetime_released: datetime | None

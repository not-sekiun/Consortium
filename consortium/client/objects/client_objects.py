from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClientConfig:
    username: str
    password: str
    remote_host: str
    remote_port: int


@dataclass
class Release:
    version: str
    codename: str  # codenames are reserved for every feature release
    datetime_released: datetime | None

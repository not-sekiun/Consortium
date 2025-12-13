from typing import Literal

from pydantic import BaseModel


class ServerConfigModel(BaseModel):
    local_host: str
    local_port: int
    remote_host_whitelist: list[str]
    remote_host_blacklist: list[str]
    server_header: str | None


class LoggingConfigModel(BaseModel):
    log_level: Literal[
        "TRACE",
        "DEBUG",
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ]
    log_file_path: str
    log_file_rotation: str | int | None
    log_file_retention: str | int | None
    colorize: bool

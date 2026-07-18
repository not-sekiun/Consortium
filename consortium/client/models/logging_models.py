from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class LoggingConfigModel(BaseModel):
    level: Literal[
        "TRACE",
        "DEBUG",
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"
    log_file: str | None = None
    rotation: str | int | None = None
    retention: str | int | None = None
    colorize: bool = True


class LoggerType(StrEnum):
    CLIENT_REST_API_LOGGER = "CLIENT_REST_API_LOGGER"
    CLIENT_WEBSOCKETS_EVENTS_API_LOGGER = "CLIENT_WEBSOCKETS_EVENTS_API_LOGGER"
    CLIENT_INTERPRETER_LOGGER = "CLIENT_INTERPRETER_LOGGER"
    CLIENT_SESSIONS_SERVICE = "CLIENT_SESSIONS_SERVICE"

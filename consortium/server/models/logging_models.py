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
    # When true, deliberate secret logging (e.g. passwords, session ids) is emitted in
    # the clear instead of redacted. Off by default: reprs are always redacted, and this
    # only ungates the explicit secret() log sites. Intended for local debugging only.
    log_secrets: bool = False


# Provide a custom logger type to color mapping. So that we can specially highlight log
# lines in the colorized terminal output for loggers that are logging from specific
# objects in the framework (this is typically all the user created objects).
class LoggerType(StrEnum):
    LISTENER_LOGGER = "LISTENER_LOGGER"
    AGENT_LOGGER = "AGENT_LOGGER"
    AGENT_TASK_LOGGER = "AGENT_TASK_LOGGER"
    GENERATOR_LOGGER = "GENERATOR_LOGGER"
    EVENT_HOOK_LOGGER = "EVENT_HOOKS_LOGGER"
    PLUGIN_LOGGER = "PLUGIN_LOGGER"
    REST_API_LOGGER = "REST_API_LOGGER"
    WEBSOCKET_EVENTS_API_LOGGER = "WEBSOCKET_EVENTS_API_LOGGER"
    SERVICE_LOGGER = "SERVICE_LOGGER"
    SERVER_LOGGER = "SERVER_LOGGER"

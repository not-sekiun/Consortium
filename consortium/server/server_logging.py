import sys
from collections import defaultdict
from datetime import datetime
from enum import StrEnum
from typing import Literal

from loguru import logger

from consortium.server.server_config import CONSORTIUM_SERVER_LOGS_DIRECTORY_PATH


# Provide a custom logger type to color mapping. So that we can specially highlight log
# lines in the colorized terminal output for loggers that are logging from specific
# objects in the framework (this is typically all the user created objects).
class LoggerType(StrEnum):
    LISTENER_LOGGER = "LISTENER_LOGGER"
    AGENT_LOGGER = "AGENT_LOGGER"
    GENERATOR_LOGGER = "GENERATOR_LOGGER"
    EVENT_HOOK_LOGGER = "EVENT_HOOKS_LOGGER"
    PLUGIN_LOGGER = "PLUGIN_LOGGER"
    API_LOGGER = "API_LOGGER"
    SERVICE_LOGGER = "SERVICE_LOGGER"


def log_formatter(record):
    logger_type_to_color_str_map = defaultdict(lambda: "<dim><white>")
    logger_type_to_color_str_map[LoggerType.LISTENER_LOGGER] = "<bold><blue>"
    logger_type_to_color_str_map[LoggerType.AGENT_LOGGER] = "<bold><red>"
    logger_type_to_color_str_map[LoggerType.GENERATOR_LOGGER] = "<bold><green>"
    logger_type_to_color_str_map[LoggerType.EVENT_HOOK_LOGGER] = "<bold><magenta>"
    logger_type_to_color_str_map[LoggerType.PLUGIN_LOGGER] = "<bold><cyan>"
    logger_type_to_color_str_map[LoggerType.API_LOGGER] = "<bold><yellow>"
    logger_type_to_color_str_map[LoggerType.SERVICE_LOGGER] = "<bold><white>"

    logger_type = record["extra"].get("logger_type")

    if not logger_type:
        color = "<dim><white>"
    else:
        color = logger_type_to_color_str_map.get(logger_type, "<dim><white>")

    # Can't use f-string here because of the loguru syntax. Also, we need to add
    # the newline character at the end of the string for formatter functions.
    return (
        "<dim><white>[{time:YYYY-MM-DDTHH:mm:ssZ}]</></> <level>{level:<8}</> "
        + color
        + "{extra[logger_name]}</></>: {message}\n"
    )


def configure_logger(
    log_level: Literal[
        "TRACE",
        "DEBUG",
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ],
):
    logger.remove()  # Remove all default loggers.
    logger.add(
        # ":" is invalid in filenames, so we replace it with the URL safe character "-".
        f"{CONSORTIUM_SERVER_LOGS_DIRECTORY_PATH}/{datetime.now().isoformat().replace(":", "-")}.log",
        format="[{time:YYYY-MM-DDTHH:mm:ssZ}] {level:<8} {extra[logger_name]}: {message}",
        level=log_level,
    )
    logger.add(
        sys.stdout,
        colorize=True,
        format=log_formatter,
        level=log_level,
    )
    logger.level("TRACE", color="<bold><cyan>")
    logger.level("DEBUG", color="<bold><green>")
    logger.level("INFO", color="<bold><blue>")
    logger.level("WARNING", color="<bold><yellow>")
    logger.level("ERROR", color="<bold><red>")
    logger.level("CRITICAL", color="<white><RED><bold>")
    logger.level("SUCCESS", color="<bold><green>")

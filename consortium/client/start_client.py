import argparse
import asyncio
import json
import sys

from loguru import logger
from pydantic import ValidationError

from consortium.client.client import Client
from consortium.client.client_config import (
    CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH,
    CONSORTIUM_LOGGING_CONFIG_JSON_FILE_PATH,
)
from consortium.client.models.client_models import ClientConfig
from consortium.client.models.logging_models import LoggingConfigModel
from consortium.client.utils.logging_utils import log_formatter


async def _start_client(arguments: argparse.Namespace) -> None:
    # Configure client from configuration file.
    if arguments.client_config is None:
        # Use relative pathing from the module to allow directory independent
        # invocation.
        client_config_filepath = str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH)
    else:
        client_config_filepath = arguments.client_config

    try:
        with open(client_config_filepath) as file:
            json_data = json.load(fp=file)
    except FileNotFoundError:
        print(
            f"Failed to start client. Could not find client configuration file at "
            f"the provided file path '{client_config_filepath}'.",
        )
        return
    except PermissionError:
        print(
            f"Failed to start client. Permission denied when attempting to read client "
            f"configuration file at '{client_config_filepath}'.",
        )
        return

    try:
        client_config = ClientConfig(**json_data)
    except ValidationError as exc:
        print(
            f"Failed to start client. The provided client configuration file "
            f"'{client_config_filepath}' does not adhere to the expected client "
            f"configuration file JSON schema: {exc}",
        )
        return

    # Configure logging from configuration file.
    if arguments.logging_config is None:
        logging_config_filepath = CONSORTIUM_LOGGING_CONFIG_JSON_FILE_PATH
    else:
        logging_config_filepath = arguments.logging_config

    try:
        with open(logging_config_filepath) as file:
            json_data = json.load(file)
        logging_config = LoggingConfigModel(
            level="DEBUG" if arguments.debug else json_data.get("level", "INFO"),
            log_file=json_data.get("log_file"),
            rotation=json_data.get("rotation", None),
            retention=json_data.get("retention", 1),
            colorize=json_data.get("colorize", True),
        )
    except FileNotFoundError:
        print(
            f"Failed to start client. Could not find the logging configuration file at "
            f"the provided file path '{logging_config_filepath}'.",
        )
        return
    except PermissionError:
        print(
            "Failed to start client. Permission denied when attempting to read the "
            f"logging configuration file at '{logging_config_filepath}'.",
        )
        return
    except ValidationError as exc:
        print(
            f"Failed to start client. The provided logging configuration file "
            f"'{logging_config_filepath}' does not adhere to the expected logging "
            f"configuration file JSON schema: {exc}",
        )
        return

    logger.remove()  # Remove all default loggers

    # Set display colors per log level
    logger.level("TRACE", color="<bold><cyan>")
    logger.level("DEBUG", color="<bold><green>")
    logger.level("INFO", color="<bold><blue>")
    logger.level("WARNING", color="<bold><yellow>")
    logger.level("ERROR", color="<bold><red>")
    logger.level("CRITICAL", color="<white><RED><bold>")
    logger.level("SUCCESS", color="<bold><green>")

    # Add default stdout logging
    logger.add(
        sys.stdout,
        format=log_formatter,
        colorize=logging_config.colorize,
        level=logging_config.level,
    )

    # Add default file based logging if specified
    if logging_config.log_file is not None:
        logger.add(
            sink=logging_config.log_file,
            level=logging_config.level,
            format=log_formatter,
            rotation=logging_config.rotation,
            retention=logging_config.retention,
            colorize=False,
        )

    await Client(client_config=client_config).run()


def main(arguments: argparse.Namespace) -> None:
    asyncio.run(_start_client(arguments))

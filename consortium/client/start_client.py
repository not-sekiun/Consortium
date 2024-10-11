import argparse
import asyncio
import json
import sys
from datetime import datetime

from loguru import logger
from pydantic import ValidationError

from consortium.client.client import Client
from consortium.client.client_config import (
    CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH,
    CONSORTIUM_CLIENT_LOGS_DIRECTORY_PATH,
)
from consortium.client.objects.client_objects import ClientConfig


async def _start_client(arguments: argparse.Namespace) -> None:
    # Load client configuration file
    if arguments.config is None:
        # Use relative pathing from the module to allow directory independent
        # invocation.
        client_config_filepath = str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH)
    else:
        client_config_filepath = arguments.config
    # TODO: Support starting the client with a disconnected interpreter when the client
    #  config file is not specified.
    try:
        with open(client_config_filepath, "r") as file:
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

    # Configure logging.
    if arguments.debug:
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    logger.remove()  # Remove all default loggers.
    logger.add(
        # We are using ISO8601 formatted datetime strings but ":" is invalid in
        # filenames, so we replace it with the character "-".
        f"{CONSORTIUM_CLIENT_LOGS_DIRECTORY_PATH}/{datetime.now().isoformat().replace(":", "-")}.log",
        format="[{time:YYYY-MM-DDTHH:mm:ssZ}] {level:<8} {extra[logger_name]}: {message}",
        level=log_level,
    )
    logger.add(
        sys.stdout,
        colorize=True,
        level=log_level,
    )
    logger.level("TRACE", color="<bold><cyan>")
    logger.level("DEBUG", color="<bold><green>")
    logger.level("INFO", color="<bold><blue>")
    logger.level("WARNING", color="<bold><yellow>")
    logger.level("ERROR", color="<bold><red>")
    logger.level("CRITICAL", color="<white><RED><bold>")
    logger.level("SUCCESS", color="<bold><green>")

    await Client(client_config=client_config).start()


def main(arguments: argparse.Namespace) -> None:
    asyncio.run(_start_client(arguments))

import argparse
import asyncio
import pathlib
import sys

from loguru import logger

from consortium.client.client import Client
from consortium.client.client_config import (
    CLIENT_CONFIG_JSON_FILE,
    CONSORTIUM_ROOT,
    LOGGING_CONFIG_JSON_FILE,
)
from consortium.client.exceptions.config_exceptions import ConfigLoadError
from consortium.client.models.client_models import ClientConfig
from consortium.client.models.logging_models import LoggingConfigModel
from consortium.client.utils.config_utils import load_config_model_from_json_file
from consortium.client.utils.logging_utils import log_formatter


async def _start_client(arguments: argparse.Namespace) -> None:
    try:
        client_config = load_config_model_from_json_file(
            path=(
                CLIENT_CONFIG_JSON_FILE
                if arguments.client_config is None
                else arguments.client_config
            ),
            model=ClientConfig,
            description="client configuration",
        )
        logging_config = load_config_model_from_json_file(
            path=(
                LOGGING_CONFIG_JSON_FILE
                if arguments.logging_config is None
                else arguments.logging_config
            ),
            model=LoggingConfigModel,
            description="logging configuration",
        )
    except ConfigLoadError as exc:
        print(f"Failed to start client. {exc}")
        return

    if arguments.debug:
        logging_config.level = "DEBUG"

    if logging_config.log_file is not None:
        path = pathlib.Path(logging_config.log_file)
        if not path.is_absolute():
            logging_config.log_file = str(CONSORTIUM_ROOT / path)

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

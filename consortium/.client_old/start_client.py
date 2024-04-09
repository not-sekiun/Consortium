import argparse
import json
import sys
from datetime import datetime

from loguru import logger

from consortium.client.client import Client
from consortium.client.client_config import (
    CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH,
    CONSORTIUM_CLIENT_LOGS_DIRECTORY_PATH,
)
from consortium.client.objects.client_objects import ClientConfig


async def main(args: argparse.Namespace) -> None:
    # Load client configuration file
    with open(str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH), "r") as file:
        json_data = json.load(fp=file)
    client_config = ClientConfig(**json_data)

    # Configure logging.
    logger.remove()  # Remove all default out of the box loggers.
    logger.add(
        # ":" is invalid in filenames, so we replace it with the URL safe character
        # "-"
        f"{CONSORTIUM_CLIENT_LOGS_DIRECTORY_PATH}/{datetime.now().isoformat().replace(":", "-")}.log",
        colorize=False,
        format="[{time:YYYY-MM-DDTHH:mm:ssZ}] {level:<8} {message}",
        level="DEBUG" if args.debug else "INFO",
    )
    logger.level("DEBUG", color="<bold><green>")
    logger.level("INFO", color="<bold><blue>")
    logger.level("WARNING", color="<bold><yellow>")
    logger.level("ERROR", color="<bold><red>")
    logger.level("CRITICAL", color="<white><RED><bold>")
    logger.add(
        sys.stdout,
        colorize=True,
        format=(
            "<dim><white>[{time:YYYY-MM-DDTHH:mm:ssZ}]</></> <level>{level:<8}</> "
            "<dim><white>{extra[logger_name]}</></>: {message}"
        ),
        level="DEBUG" if args.debug else "INFO",
    )

    await Client(client_config=client_config).run_client()

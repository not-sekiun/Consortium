import argparse
import json
import sys
from datetime import datetime

from loguru import logger

from consortium.server.models.server_models import ServerConfigModel
from consortium.server.server_config import (
    CONSORTIUM_SERVER_CONFIG_JSON_FILE_PATH,
    CONSORTIUM_SERVER_LOGS_DIRECTORY_PATH,
)


def main(arguments: argparse.Namespace) -> None:
    # Load server configuration file
    with open(str(CONSORTIUM_SERVER_CONFIG_JSON_FILE_PATH), "r") as file:
        json_data = json.load(fp=file)
    server_config = ServerConfigModel(**json_data)

    # Configure logging.
    logger.remove()  # Remove all default out of the box loggers.
    logger.add(
        # ":" is invalid in filenames, so we replace it with the URL safe character
        # "-"
        f"{CONSORTIUM_SERVER_LOGS_DIRECTORY_PATH}/{datetime.now().isoformat().replace(":", "-")}.log",
        colorize=False,
        format="[{time:YYYY-MM-DDTHH:mm:ssZ}] {level:<8} {message}",
        level="DEBUG" if arguments.debug else "INFO",
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
        level="DEBUG" if arguments.debug else "INFO",
    )

    # We are importing both Server and server_singletons within the function here
    # because we need to configure the logger first. server_singletons contains services
    # that run at import time and automatically log output at import time. Server
    # contains further imports that themselves reference server_singletons too
    import consortium.server.server_singletons as server_singletons
    from consortium.server.server import Server

    # configure server and create a reference to it in the server singletons module
    server_singletons.server = Server(
        server_config=server_config,
    )
    server_singletons.server.start_server()

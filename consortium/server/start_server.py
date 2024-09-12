import argparse
import json

from consortium.server.models.server_models import ServerConfigModel
from consortium.server.server_config import CONSORTIUM_SERVER_CONFIG_JSON_FILE_PATH
from consortium.server.server_logging import configure_logger


def main(arguments: argparse.Namespace) -> None:
    # Load server configuration file
    if arguments.config is None:
        # Use relative pathing from the module to allow directory independent
        # invocation.
        server_config_filepath = str(CONSORTIUM_SERVER_CONFIG_JSON_FILE_PATH)
    else:
        server_config_filepath = arguments.config

    # TODO: Error handling for file loading.
    with open(server_config_filepath, "r") as file:
        json_data = json.load(fp=file)
    server_config = ServerConfigModel(**json_data)

    if arguments.debug:
        configure_logger(log_level="DEBUG")
    else:
        configure_logger(log_level=server_config.log_level)

    # We are importing both Server and server_singletons within the function here
    # because we need to configure the logger first. server_singletons contains services
    # that run at import time and automatically log output at import time. The server
    # object contains further imports that themselves reference server_singletons too.
    import consortium.server.server_singletons as server_singletons
    from consortium.server.server import Server

    # Configure server and create a reference to it in the server singletons module.
    server_singletons.server = Server(server_config=server_config)
    server_singletons.server.start_server()

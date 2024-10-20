import argparse
import json

from pydantic import ValidationError

import consortium.server.server_reloader as server_reloader
from consortium.server.models.server_models import ServerConfigModel
from consortium.server.server_config import CONSORTIUM_SERVER_CONFIG_JSON_FILE_PATH
from consortium.server.server_logging import configure_logger


def main(arguments: argparse.Namespace) -> None:
    # First thing we check is if reloading is enabled. If the reload flag is set, we
    # essentially just run the entire server again (through the entry point script)
    # with all the same arguments as before just without the reload flag (otherwise
    # this exact same behaviour would be called again recursively). The server this
    # time is run in a subprocess that is terminated and started whenever file changes
    # are detected.
    if arguments.reload:
        server_reloader.main()
        return
    # Load server configuration file
    if arguments.config is None:
        # Use relative pathing from the module to allow directory independent
        # invocation.
        server_config_filepath = str(CONSORTIUM_SERVER_CONFIG_JSON_FILE_PATH)
    else:
        server_config_filepath = arguments.config
    try:
        with open(server_config_filepath, "r") as file:
            json_data = json.load(fp=file)
    except FileNotFoundError:
        print(
            f"Failed to start server. Could not find server configuration file at "
            f"the provided file path '{server_config_filepath}'.",
        )
        return
    except PermissionError:
        print(
            "Failed to start client. Permission denied when attempting to read server "
            f"configuration file at '{server_config_filepath}'.",
        )
        return
    try:
        server_config = ServerConfigModel(**json_data)
    except ValidationError as exc:
        print(
            f"Failed to start server. The provided server configuration file "
            f"'{server_config_filepath}' does not adhere to the expected server "
            f"configuration file JSON schema: {exc}",
        )
        return

    # Configure logging.
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

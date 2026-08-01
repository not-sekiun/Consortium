import argparse
import asyncio
import json
import pathlib

from pydantic import ValidationError

import consortium.server.server_component_dependency_syncer as server_component_dependency_syncer
import consortium.server.server_reloader as server_reloader
import consortium.server.server_singletons as server_singletons
from consortium.server.models.logging_models import LoggingConfigModel
from consortium.server.models.server_models import ServerConfigModel
from consortium.server.server import Server


async def _start_server(arguments: argparse.Namespace) -> None:
    await server_component_dependency_syncer.main()

    # Resolve necessary file and directory paths first. We dont do this through the
    # `PathsService` because that service depends on the logging service being
    # initialized first, which we are doing here.
    consortium_root = pathlib.Path(__file__).parents[2]

    # First thing we check is if reloading is enabled. If the reload flag is set, we
    # essentially just run the entire server again (through the entry point script)
    # with all the same arguments as before just without the reload flag (otherwise
    # this exact same behaviour would be called again recursively). The server this
    # time is run in a subprocess that is terminated and started whenever file changes
    # are detected.
    if arguments.reload:
        server_reloader.main(consortium_root=consortium_root)
        return

    # Configure server from configuration file.
    if arguments.server_config is None:
        # Use relative pathing from the module to allow directory independent
        # invocation.
        server_config_filepath = (
            consortium_root / "data" / "server" / "server_config.json"
        )
    else:
        server_config_filepath = arguments.server_config

    try:
        with open(server_config_filepath) as file:
            json_data = json.load(file)
        server_config = ServerConfigModel(
            local_host=json_data.get("local_host", "0.0.0.0"),
            local_port=json_data.get("local_port", 9999),
            remote_host_whitelist=json_data.get("remote_host_whitelist", []),
            remote_host_blacklist=json_data.get("remote_host_blacklist", []),
            server_header=json_data.get("server_header", None),
        )
    except FileNotFoundError:
        print(
            f"Failed to start server. Could not find the server configuration file at "
            f"the provided file path '{server_config_filepath}'.",
        )
        return
    except PermissionError:
        print(
            "Failed to start server. Permission denied when attempting to read the "
            f"server configuration file at '{server_config_filepath}'.",
        )
        return
    except ValidationError as exc:
        print(
            f"Failed to start server. The provided server configuration file "
            f"'{server_config_filepath}' does not adhere to the expected server "
            f"configuration file JSON schema: {exc}",
        )
        return

    # Configure logging from configuration file.
    if arguments.logging_config is None:
        logging_config_filepath = (
            consortium_root / "data" / "server" / "logging_config.json"
        )
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
            f"Failed to start server. Could not find the logging configuration file at "
            f"the provided file path '{logging_config_filepath}'.",
        )
        return
    except PermissionError:
        print(
            "Failed to start server. Permission denied when attempting to read the "
            f"logging configuration file at '{logging_config_filepath}'.",
        )
        return
    except ValidationError as exc:
        print(
            f"Failed to start server. The provided logging configuration file "
            f"'{logging_config_filepath}' does not adhere to the expected logging "
            f"configuration file JSON schema: {exc}",
        )
        return

    if logging_config.log_file is not None:
        path = pathlib.Path(logging_config.log_file)
        if not path.is_absolute():
            logging_config.log_file = str(consortium_root / path)

    try:
        server_singletons.logging_service.configure_default_logging(
            logging_config=logging_config
        )
    # Loguru raises `ValueError` for invalid rotation and retention values.
    except ValueError as exc:
        print(
            f"Failed to start server. The provided logging configuration file "
            f"'{logging_config_filepath}' contains invalid values: {exc}",
        )
        return

    # Create server and create a reference to it in the server singletons module before
    # starting it
    server_singletons.server = Server(server_config=server_config)
    await server_singletons.server.start_server()


def main(arguments: argparse.Namespace) -> None:
    try:
        asyncio.run(_start_server(arguments=arguments))
    except KeyboardInterrupt:
        pass

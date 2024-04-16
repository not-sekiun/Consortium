import json
from argparse import ArgumentParser

import jsonschema
from aiohttp.client_exceptions import ClientConnectionError

import consortium.client.client_singletons as client_singletons
from consortium.client.client_config import CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH
from consortium.client.client_connection import ClientConnection
from consortium.client.client_exceptions import (
    AlreadyLoggedInError,
    FailedToLoginError,
    InvalidServerLoginResponseError,
)
from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_objects import ClientConfig
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import print_error, print_success
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter

client_connections_service = client_singletons.client_connections_service


class ConnectCommand(BaseCommand):
    name = "connect"
    description = "Connect to a server."
    epilog = argparse_epilog_formatter(
        """
        Example:
            connect -c my/path/to/client_config.json  # Connect using config file
            connect -u username -p password -rh server.com -rp 1234  # Connect manually
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-c",
            "--config",
            help="Filepath of client config JSON file to load client config data from. By default, the client config JSON file is loaded from the client data folder.",
            nargs="?",
            const=str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH),
        )
        parser.add_argument(
            "-rh",
            "--remote-host",
            help="The remote host to connect to.",
        )
        parser.add_argument(
            "-rp",
            "--remote-port",
            help="The remote port to connect to.",
        )
        parser.add_argument(
            "-u",
            "--username",
            help="The username to authenticate with.",
        )
        parser.add_argument(
            "-p",
            "--password",
            help="The password to authenticate with.",
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            # Perform custom checking of arguments
            if (
                not parsed_args.config
                and not all(
                    [
                        parsed_args.remote_host,
                        parsed_args.remote_port,
                        parsed_args.username,
                        parsed_args.password,
                    ],
                )
                or parsed_args.config
                and all(
                    [
                        parsed_args.remote_host,
                        parsed_args.remote_port,
                        parsed_args.username,
                        parsed_args.password,
                    ],
                )
            ):
                self.parser.error(
                    "Either -c/--config or all of -rh/--remote-host, -rp/--remote-port, -u/--username, and -p/--password must be provided but not both at the same time.",
                )

            if parsed_args.config:
                client_config_file_json_schema = {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "remote_host": {"type": "string"},
                        "remote_port": {"type": "number"},
                    },
                    "required": ["remote_host", "remote_port", "username", "password"],
                }

                try:
                    with open(parsed_args.config, "r") as file:
                        config_data = json.load(fp=file)
                    jsonschema.validate(config_data, client_config_file_json_schema)
                except FileNotFoundError as exc:
                    print_error(f"The config filepath supplied does not exist: {exc}")
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
                except PermissionError as exc:
                    print_error(
                        f"Insufficient permissions to read the config file: {exc}",
                    )
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
                except json.decoder.JSONDecodeError:
                    print_error("The config file does not contain valid JSON data")
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
                except jsonschema.ValidationError as exc:
                    print_error(
                        f"The config file's JSON data is not of a valid server config format: {exc}",
                    )
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

                client_config = ClientConfig(
                    remote_host=config_data["remote_host"],
                    remote_port=config_data["remote_port"],
                    username=config_data["username"],
                    password=config_data["password"],
                )
            else:
                client_config = ClientConfig(
                    remote_host=parsed_args.remote_host,
                    remote_port=parsed_args.remote_port,
                    username=parsed_args.username,
                    password=parsed_args.password,
                )

            try:
                client_connection = ClientConnection(client_config=client_config)
                await client_connection.login()
            # AlreadyLoggedInError should not be raised unless a programmer error is
            # made.
            except (
                FailedToLoginError,
                InvalidServerLoginResponseError,
                AlreadyLoggedInError,
                ClientConnectionError,
            ) as exc:
                print_error(f"Failed to login to server: {exc}")
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            client_connections_service.add_client_connection(
                client_connection=client_connection,
            )
            print_success(
                f"Successfully logged in to server: {client_config.remote_host}:{client_config.remote_port}",
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

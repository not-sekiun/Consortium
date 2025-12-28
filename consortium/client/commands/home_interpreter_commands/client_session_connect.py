import json
from argparse import ArgumentParser

import jsonschema

import consortium.client.client_singletons as client_singletons
from consortium.client.client_config import CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionConnectionError,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class ConnectCommand(BaseCommand):
    name = "connect"
    description = "Connect to a Consortium server, creating a new client session"
    epilog = format_argparse_epilog(
        """
        Examples:
          connect -c  # Connect using the default filepath to the client configuration file.
          connect -c path/to/client_config.json  # Connect using a custom configuration file.
          connect -u username -p password -rh server.com -rp 1234  # Connect through manually provided connection details.
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-c",
            "--config",
            help=(
                "Filepath of the client configuration file to use when connecting to a "
                "server. By default the configuration file from "
                "`data/client/client_config.json` is used."
            ),
            nargs="?",
            const=str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH),
        )
        parser.add_argument(
            "-rh",
            "--remote-host",
            help="Remote host of the Consortium server to connect to.",
        )
        parser.add_argument(
            "-rp",
            "--remote-port",
            help="Remote port of the Consortium server to connect to.",
            type=int,
        )
        parser.add_argument(
            "-u", "--username", help="Username of the account to login as."
        )
        parser.add_argument(
            "-p", "--password", help="Password of the account to login with."
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            # Perform custom checking of arguments to ensure that if a config file is
            # not passed or of the connection details must be provided.
            if not parsed_args.config and not all(
                [
                    parsed_args.remote_host,
                    parsed_args.remote_port,
                    parsed_args.username,
                    parsed_args.password,
                ],
            ):
                self.parser.error(
                    "All of -rh/--remote-host, -rp/--remote-port, -u/--username, and "
                    "-p/--password must be provided if the client configuration file is"
                    "not provided.",
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
                    "additionalProperties": False,
                }

                try:
                    with open(parsed_args.config) as file:
                        config_data = json.load(fp=file)
                    jsonschema.validate(config_data, client_config_file_json_schema)
                except FileNotFoundError as exc:
                    print_error(f"The config filepath supplied does not exist: {exc}")
                    return ReturnStatus(type=ReturnStatusType.CONTINUE)
                except PermissionError as exc:
                    print_error(
                        f"Insufficient permissions to read the config file: {exc}",
                    )
                    return ReturnStatus(type=ReturnStatusType.CONTINUE)
                except json.decoder.JSONDecodeError:
                    print_error("The config file does not contain valid JSON data")
                    return ReturnStatus(type=ReturnStatusType.CONTINUE)
                except jsonschema.ValidationError as exc:
                    print_error(
                        f"The config file's JSON data is not of a valid server config "
                        f"format: {exc}",
                    )
                    return ReturnStatus(type=ReturnStatusType.CONTINUE)

                username = parsed_args.username or config_data["username"]
                password = parsed_args.password or config_data["password"]
                remote_host = parsed_args.remote_host or config_data["remote_host"]
                remote_port = parsed_args.remote_port or config_data["remote_port"]
            else:
                username = parsed_args.username
                password = parsed_args.password
                remote_host = parsed_args.remote_host
                remote_port = parsed_args.remote_port

            try:
                client_session = client_sessions_service.create_and_add_client_session(
                    username=username,
                    password=password,
                    remote_host=remote_host,
                    remote_port=remote_port,
                )
                await (
                    client_sessions_service.connect_client_session_by_client_session_id(
                        client_session_id=str(client_session.client_session_id),
                    )
                )
                print_success(
                    f"Connected to server {remote_host}:{remote_port} as '{username}'"
                )
            except ClientSessionConnectionError as exc:
                print_error(exc)
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)

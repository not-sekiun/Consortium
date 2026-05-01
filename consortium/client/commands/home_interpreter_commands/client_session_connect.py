import json
from argparse import ArgumentParser

import jsonschema

import consortium.client.client_singletons as client_singletons
from consortium.client.client_config import CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionConnectionError,
)
from consortium.client.exceptions.rest_api_exceptions import (
    RestAPIAuthenticationError,
)
from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info, print_success

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
            default=str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH),
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
    ) -> InterpreterSignal:
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
                    "-p/--password must be provided if the client configuration file "
                    "is not provided.",
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
                except FileNotFoundError:
                    print_error(
                        f"Failed to read the provided client configuration file "
                        f"'{parsed_args.config}'. The file path supplied was not "
                        f"found.",
                    )
                    return ContinueSignal()
                except PermissionError as exc:
                    print_error(
                        f"Failed to read the provided client configuration file "
                        f"'{parsed_args.config}'. Insufficient permissions to read the "
                        f"file: {exc}",
                    )
                    return ContinueSignal()
                except json.decoder.JSONDecodeError:
                    print_error(
                        f"Failed to read the provided client configuration file "
                        f"'{parsed_args.config}'. The configuration file does not "
                        f"contain valid JSON data"
                    )
                    return ContinueSignal()
                except jsonschema.ValidationError as exc:
                    print_error(
                        f"Failed to read the provided client configuration file "
                        f"'{parsed_args.config}'. The configuration file's JSON data "
                        f"does not conform to the expected JSON schema: {exc}",
                    )
                    return ContinueSignal()

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
                client_session = await client_sessions_service.create_client_session(
                    username=username,
                    password=password,
                    remote_host=remote_host,
                    remote_port=remote_port,
                )
                print_success(
                    f"Connected to server {remote_host}:{remote_port} as '{username}'"
                )
                print_info(f"New client session created: {client_session}")
            except (ClientSessionConnectionError, RestAPIAuthenticationError) as exc:
                print_error(exc)
        except SystemExit:
            pass

        return ContinueSignal()

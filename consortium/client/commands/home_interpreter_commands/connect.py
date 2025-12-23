import json
from argparse import ArgumentParser

import jsonschema

import consortium.client.client_singletons as client_singletons
from consortium.client.client_config import CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionConnectionError,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class ConnectCommand(BaseCommand):
    name = "connect"
    description = (
        "Create a new client session to a Consortium server using a configuration "
        "file or by manually specifying connection details."
    )
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
                "The filepath to a configuration JSON file containing the client "
                "settings specifying the remote host, remote port, username, and "
                "password to use when connecting to the Consortium server. If not "
                "provided, the default filepath to the configuration file is used."
            ),
            nargs="?",
            const=str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH),
            metavar="CONFIG_FILEPATH",
        )
        parser.add_argument(
            "-rh",
            "--remote-host",
            help=(
                "The remote hostname or IP address of the Consortium server to connect "
                "to."
            ),
            metavar="HOSTNAME/IP",
        )
        parser.add_argument(
            "-rp",
            "--remote-port",
            help="The port of the Consortium server to connect to.",
            metavar="PORT",
            type=int,
        )
        parser.add_argument(
            "-u",
            "--username",
            help=(
                "The username of the account to login to when connecting to the "
                "Consortium server."
            ),
            metavar="USERNAME",
        )
        parser.add_argument(
            "-p",
            "--password",
            help=(
                "The password of the account to login to when connecting to the "
                "Consortium server."
            ),
            metavar="PASSWORD",
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            # Perform custom checking of arguments to ensure that either a config file
            # or all of the connection details are provided but not both.
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
                    "Either -c/--config or all of -rh/--remote-host, "
                    "-rp/--remote-port, -u/--username, and -p/--password must be "
                    "provided but not both simultaneously.",
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
                    with open(parsed_args.config) as file:
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
                        f"The config file's JSON data is not of a valid server config "
                        f"format: {exc}",
                    )
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

                username = config_data["username"]
                password = config_data["password"]
                remote_host = config_data["remote_host"]
                remote_port = config_data["remote_port"]
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
                await client_sessions_service.connect_client_session(
                    client_session_id=str(client_session.client_session_id),
                )
                print_success(
                    f"Successfully logged into server "
                    f"{remote_host}:{remote_port} as '{username}'.",
                )
            except ClientSessionConnectionError as exc:
                print_error(exc)
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

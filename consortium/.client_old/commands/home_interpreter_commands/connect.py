import argparse
import json

import jsonschema

import consortium.client.client_singletons as client_singletons
from consortium.client.client_config import CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH
from consortium.client.client_exceptions import FailedToLoginError
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.client_objects import ClientConfig
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class ConnectCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Connect to a server to create a new server session.",
            prog="connect",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    connect -c my/path/to/client_config.json  # Connect using config file
                    connect -u username -p password -rh server.com -rp 1234  # Connect manually
                """,
            ),
        )

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

        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus:
        try:
            parsed_args = self._parser.parse_args(
                interpreter_command.arguments,
            )

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
                self._parser.error(
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
                    return ContinueReturnStatus()
                except PermissionError as exc:
                    print_error(
                        f"Insufficient permissions to read the config file: {exc}",
                    )
                    return ContinueReturnStatus()
                except json.decoder.JSONDecodeError:
                    print_error("The config file does not contain valid JSON data")
                    return ContinueReturnStatus()
                except jsonschema.ValidationError as exc:
                    print_error(
                        f"The config file's JSON data is not of a valid server config format: {exc}",
                    )
                    return ContinueReturnStatus()

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
                client_session = ClientSession(client_config=client_config)
                await client_session.login()
            except FailedToLoginError as exc:
                print_error(f"Failed to login: {exc}")
                return ContinueReturnStatus()

            client_sessions_service.add_client_session(client_session)
            print_success(
                f"Successfully logged in to server: {client_config.remote_host}:{client_config.remote_port}",
            )
        except SystemExit:
            pass

        return ContinueReturnStatus()

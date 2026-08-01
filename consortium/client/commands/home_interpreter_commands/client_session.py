import json
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter

import jsonschema

import consortium.client.client_singletons as client_singletons
from consortium.client.client_config import CLIENT_CONFIG_JSON_FILE
from consortium.client.client_session import ClientSession
from consortium.client.exceptions.client_session_exceptions import (
    BaseClientSessionError,
)
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionNotFoundError,
)
from consortium.client.models.context_models import AnyContext, ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    ExitClientSessionSignal,
    InterpreterSignal,
    SwitchClientSessionSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.client_session_command_utils import (
    describe_client_session,
    disconnect_client_session,
    display_all_client_sessions,
    display_client_session_info,
    rename_client_session,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import (
    print_error,
    print_info,
    print_success,
)
from consortium.client.utils.ui_utils import with_spinner

client_sessions_service = client_singletons.client_sessions_service


# Client sessions are managed from anywhere in the client, connected or not, so this
# command is typed against both context types and registered as a core command. The
# disconnected interpreter registers its own variant of it in place of this one.
class SessionCommand(BaseCommand[AnyContext]):
    name = "session"
    description = "Manage client sessions through its sub-commands"
    epilog = format_argparse_epilog(
        """
        Examples:
          session connect
          session list
          session interact 123e4567-e89b-12d3-a456-426614174000
          session info
          session rename 123e4567-e89b-12d3-a456-426614174000 "New name"
          session describe 123e4567-e89b-12d3-a456-426614174000 "New description"
          session disconnect

        Notes:
          Every sub-command carries its own help, for example:
            session connect --help
        """,
    )
    autocompletes = {
        "connect": None,
        "disconnect": Autocomplete.CLIENT_SESSION_ID,
        "info": Autocomplete.CLIENT_SESSION_ID,
        "interact": Autocomplete.CLIENT_SESSION_ID,
        "list": None,
        "describe": Autocomplete.CLIENT_SESSION_ID,
        "rename": Autocomplete.CLIENT_SESSION_ID,
    }
    # Help and examples for every sub-command that takes a client session ID, declared
    # as class attributes so that the disconnected interpreter's variant of this command
    # can require that ID rather than defaulting to the current client session without
    # having to redeclare every sub-parser. `client_session_id_nargs` of `None` is
    # argparse's own default of a single required positional.
    client_session_id_nargs: str | None = "?"
    disconnect_help = (
        "Disconnect the current client session, or a specific client session by its ID."
    )
    disconnect_client_session_id_help = (
        "ID of the client session to disconnect (defaults to the current client "
        "session if not provided)."
    )
    disconnect_epilog = format_argparse_epilog(
        """
        Examples:
          session disconnect  # Disconnects the current client session if the client session ID is not specified.
          session disconnect 123e4567-e89b-12d3-a456-426614174000
        """,
    )
    info_help = (
        "Display information for the current client session, or for a specific client "
        "session by its ID."
    )
    info_client_session_id_help = (
        "ID of the client session to display information for (defaults to the current "
        "client session if not provided)."
    )
    info_epilog = format_argparse_epilog(
        """
        Examples:
          session info  # Displays information for the current client session if the client session ID is not specified.
          session info -p  # Displays password
          session info 123e4567-e89b-12d3-a456-426614174000
        """,
    )
    describe_help = (
        "Set the description of the current client session, or of a specific client "
        "session by its ID."
    )
    describe_client_session_id_help = (
        "ID of the client session whose description should be changed (defaults to the "
        "current client session if not provided)."
    )
    describe_epilog = format_argparse_epilog(
        """
        Examples:
          session describe "New description"  # Changes the description of the current client session if the client session ID is not specified.
          session describe 123e4567-e89b-12d3-a456-426614174000 "New description"
        """,
    )
    rename_help = (
        "Set the name of the current client session, or of a specific client session "
        "by its ID."
    )
    rename_client_session_id_help = (
        "ID of the client session to rename (defaults to the current client session if "
        "not provided)."
    )
    rename_epilog = format_argparse_epilog(
        """
        Examples:
          session rename "New name"  # Renames the current client session if the client session ID is not specified.
          session rename 123e4567-e89b-12d3-a456-426614174000 "New name"
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # connect sub-command. Held onto so that the custom checking of its arguments
        # can be reported against the sub-parser they were declared on rather than
        # against the `session` parser itself.
        self.connect_parser = subparsers.add_parser(
            "connect",
            help="Connect to a Consortium server, creating a new client session.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  session connect  # Connect using the default filepath to the client configuration file.
                  session connect -c path/to/client_config.json  # Connect using a custom configuration file.
                  session connect -u username -p password -rh server.com -rp 1234  # Connect through manually provided connection details.
                """,
            ),
        )
        self.connect_parser.add_argument(
            "-c",
            "--config",
            help=(
                "Filepath of the client configuration file to use when connecting to a "
                "server. By default the configuration file from "
                "`data/client/client_config.json` is used."
            ),
            nargs="?",
            default=str(CLIENT_CONFIG_JSON_FILE),
        )
        self.connect_parser.add_argument(
            "-rh",
            "--remote-host",
            help="Remote host of the Consortium server to connect to.",
        )
        self.connect_parser.add_argument(
            "-rp",
            "--remote-port",
            help="Remote port of the Consortium server to connect to.",
            type=int,
        )
        self.connect_parser.add_argument(
            "-u", "--username", help="Username of the account to login as."
        )
        self.connect_parser.add_argument(
            "-p", "--password", help="Password of the account to login with."
        )

        # disconnect sub-command
        parser_disconnect = subparsers.add_parser(
            "disconnect",
            help=self.disconnect_help,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=self.disconnect_epilog,
        )
        parser_disconnect.add_argument(
            "client_session_id",
            help=self.disconnect_client_session_id_help,
            nargs=self.client_session_id_nargs,
            default=None,
        )

        # info sub-command
        parser_info = subparsers.add_parser(
            "info",
            help=self.info_help,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=self.info_epilog,
        )
        parser_info.add_argument(
            "client_session_id",
            help=self.info_client_session_id_help,
            nargs=self.client_session_id_nargs,
            default=None,
        )
        parser_info.add_argument(
            "-p",
            "--password",
            help="Display the password of the client session.",
            action="store_true",
            default=False,
        )

        # interact sub-command
        parser_interact = subparsers.add_parser(
            "interact",
            help="Interact with a client session by its ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  session interact 123e4567-e89b-12d3-a456-426614174000
                """,
            ),
        )
        parser_interact.add_argument(
            "client_session_id",
            help="ID of the client session to interact with.",
        )

        # list sub-command
        subparsers.add_parser(
            "list",
            help="List all client sessions along with their essential information.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  session list
                """,
            ),
        )

        # describe sub-command
        parser_describe = subparsers.add_parser(
            "describe",
            help=self.describe_help,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=self.describe_epilog,
        )
        parser_describe.add_argument(
            "client_session_id",
            help=self.describe_client_session_id_help,
            nargs=self.client_session_id_nargs,
            default=None,
        )
        parser_describe.add_argument(
            "description",
            help="New description for the client session.",
        )

        # rename sub-command
        parser_rename = subparsers.add_parser(
            "rename",
            help=self.rename_help,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=self.rename_epilog,
        )
        parser_rename.add_argument(
            "client_session_id",
            help=self.rename_client_session_id_help,
            nargs=self.client_session_id_nargs,
            default=None,
        )
        parser_rename.add_argument(
            "name",
            help="New name for the client session.",
        )

    # The client session ID every sub-command that takes one operates on. When it is
    # omitted the client session of the current interpreter is used, which is why the
    # disconnected interpreter's variant of this command requires it outright: a
    # disconnected context carries no client session to fall back on.
    @staticmethod
    def _resolve_client_session_id(
        parsed_args: Namespace,
        context: AnyContext,
    ) -> str:
        if parsed_args.client_session_id is not None:
            return parsed_args.client_session_id
        return str(context.client_session.client_session_id)

    @with_spinner()
    async def _connect(
        self, username: str, password: str, remote_host: str, remote_port: int
    ) -> ClientSession:
        return await client_sessions_service.create_client_session(
            username=username,
            password=password,
            remote_host=remote_host,
            remote_port=remote_port,
        )

    async def _handle_connect_sub_command(
        self,
        parsed_args: Namespace,
    ) -> InterpreterSignal:
        # Perform custom checking of arguments to ensure that if a config file is not
        # passed then all of the connection details must be provided.
        if not parsed_args.config and not all(
            [
                parsed_args.remote_host,
                parsed_args.remote_port,
                parsed_args.username,
                parsed_args.password,
            ],
        ):
            self.connect_parser.error(
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
            except FileNotFoundError, IsADirectoryError:
                print_error(
                    f"Failed to read the provided client configuration file "
                    f"'{parsed_args.config}'. The file path supplied was not "
                    f"found.",
                )
                return ContinueSignal()
            except PermissionError:
                print_error(
                    f"Failed to read the provided client configuration file "
                    f"'{parsed_args.config}'. Insufficient permissions to read the "
                    f"file.",
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
            client_session = await self._connect(
                username=username,
                password=password,
                remote_host=remote_host,
                remote_port=remote_port,
            )
        except BaseClientSessionError as exc:
            print_error(
                f"Failed to login to server at "
                f"{remote_host}:{remote_port} as '{username}'.",
                exc=exc,
            )
            return ContinueSignal()

        print_success(
            f"Connected to server {remote_host}:{remote_port} as '{username}'"
        )
        print_info(f"New client session created: {client_session}")

        return ContinueSignal()

    async def _handle_disconnect_sub_command(
        self,
        parsed_args: Namespace,
        context: AnyContext,
    ) -> InterpreterSignal:
        client_session_id = self._resolve_client_session_id(
            parsed_args=parsed_args,
            context=context,
        )

        await disconnect_client_session(client_session_id=client_session_id)

        # Only the interpreter whose own client session was just disconnected has to be
        # torn down, every other client session can be disconnected in place.
        if isinstance(context, ConnectedContext) and client_session_id == str(
            context.client_session.client_session_id
        ):
            return ExitClientSessionSignal()

        return ContinueSignal()

    async def _handle_info_sub_command(
        self,
        parsed_args: Namespace,
        context: AnyContext,
    ) -> InterpreterSignal:
        await display_client_session_info(
            client_session_id=self._resolve_client_session_id(
                parsed_args=parsed_args,
                context=context,
            ),
            show_password=parsed_args.password,
        )

        return ContinueSignal()

    @staticmethod
    async def _handle_interact_sub_command(
        parsed_args: Namespace,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            client_session = (
                client_sessions_service.get_client_session_by_client_session_id(
                    parsed_args.client_session_id,
                )
            )
        except ClientSessionNotFoundError as exc:
            print_error(str(exc))
            return ContinueSignal()

        if (
            isinstance(context, ConnectedContext)
            and client_session is context.client_session
        ):
            print_error(f"Already interacting with client session: {client_session}")
            return ContinueSignal()

        print_success(f"Interacting with client session: {client_session}")

        return SwitchClientSessionSignal(client_session=client_session)

    async def _handle_list_sub_command(self) -> InterpreterSignal:
        display_all_client_sessions()

        return ContinueSignal()

    async def _handle_describe_sub_command(
        self,
        parsed_args: Namespace,
        context: AnyContext,
    ) -> InterpreterSignal:
        describe_client_session(
            client_session_id=self._resolve_client_session_id(
                parsed_args=parsed_args,
                context=context,
            ),
            description=parsed_args.description,
        )

        return ContinueSignal()

    async def _handle_rename_sub_command(
        self,
        parsed_args: Namespace,
        context: AnyContext,
    ) -> InterpreterSignal:
        rename_client_session(
            client_session_id=self._resolve_client_session_id(
                parsed_args=parsed_args,
                context=context,
            ),
            name=parsed_args.name,
        )

        return ContinueSignal()

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            match parsed_args.sub_command:
                case "connect":
                    return await self._handle_connect_sub_command(
                        parsed_args=parsed_args,
                    )
                case "disconnect":
                    return await self._handle_disconnect_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "info":
                    return await self._handle_info_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "interact":
                    return await self._handle_interact_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "list":
                    return await self._handle_list_sub_command()
                case "describe":
                    return await self._handle_describe_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "rename":
                    return await self._handle_rename_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case _:
                    raise AssertionError(
                        f"Unknown session sub-command '{parsed_args.sub_command}'",
                    )
        except SystemExit:
            pass

        return ContinueSignal()

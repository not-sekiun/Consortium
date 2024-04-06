import argparse

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class RenameClientSessionCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Rename a specific client session.",
            prog="rename_client_session",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    rename_client_session 123e4567-e89b-12d3-a456-42661417400 "Client Session Name"  # Rename a client session with client session ID 123e4567-e89b-12d3-a456-42661417400 to "Client Session Name"
                """,
            ),
        )
        parser.add_argument(
            "client_session_id",
            help="Client session ID of the client session to rename.",
            nargs=1,
        )
        parser.add_argument(
            "name",
            help="Name to rename the client session to.",
            nargs=1,
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

            try:
                client_session = (
                    client_sessions_service.get_client_session_by_client_session_id(
                        client_session_id=parsed_args.client_session_id[0],
                    )
                )
                client_session.name = parsed_args.name[0]
                print_success(
                    f'Renamed client session {client_session} to: "{parsed_args.name[0]}"',
                )
            except ValueError:
                print_error(
                    f"Invalid client session ID: {parsed_args.client_session_id[0]}",
                )
        except SystemExit:
            pass

        return ContinueReturnStatus()

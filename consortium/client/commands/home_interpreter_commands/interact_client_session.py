import argparse

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
    SwitchClientSessionReturnStatus,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class InteractClientSessionCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Interact with a specific client session.",
            prog="interact_client_session",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    interact_client_session 123e4567-e89b-12d3-a456-42661417400  # Interact with client session with client session ID 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser.add_argument(
            "client_session_id",
            help="Client session ID of the client session to interact with.",
            nargs=1,
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus | SwitchClientSessionReturnStatus:
        try:
            parsed_args = self._parser.parse_args(
                interpreter_command.arguments,
            )

            if parsed_args.client_session_id[0] == str(
                client_session.client_session_id,
            ):
                print_error(
                    "Already interacting with that client session",
                )
            else:
                try:
                    target_client_session = (
                        client_sessions_service.get_client_session_by_client_session_id(
                            parsed_args.client_session_id[0],
                        )
                    )
                    print_success(
                        f"Interacting with client session: {target_client_session}",
                    )
                    return SwitchClientSessionReturnStatus(
                        client_session_id=parsed_args.client_session_id[0],
                    )
                except ValueError:
                    print_error(
                        f"Invalid client session ID: {parsed_args.client_session_id[0]}",
                    )
        except SystemExit:
            pass

        return ContinueReturnStatus()

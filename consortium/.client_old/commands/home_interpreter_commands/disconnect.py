import argparse

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    ExitClientSessionReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class DisconnectCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Disconnect from the current client session or a specific client session.",
            prog="disconnect",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    disconnect  # Disconnect the current client session
                    disconnect 123e4567-e89b-12d3-a456-42661417400  # Disconnect the client session with client session ID 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser.add_argument(
            "client_session_id",
            help="Client session ID of the client session to disconnect. If no client session ID is provided, the current client session is disconnected.",
            nargs="?",
            default=None,
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus | ExitClientSessionReturnStatus:
        try:
            parsed_args = self._parser.parse_args(
                interpreter_command.arguments,
            )

            if parsed_args.client_session_id:
                try:
                    target_client_session = (
                        client_sessions_service.get_client_session_by_client_session_id(
                            parsed_args.client_session_id,
                        )
                    )
                except ValueError as exc:
                    print_error(str(exc))
                    return ContinueReturnStatus()
            else:
                target_client_session = client_session

            try:
                await target_client_session.logout()
                client_sessions_service.remove_client_session(target_client_session)
                print_success(
                    f"Disconnected client session: {target_client_session}",
                )
                if target_client_session == client_session:
                    return ExitClientSessionReturnStatus()
            except ValueError as exc:
                print_error(str(exc))
                return ContinueReturnStatus()
        except SystemExit:
            pass

        return ContinueReturnStatus()

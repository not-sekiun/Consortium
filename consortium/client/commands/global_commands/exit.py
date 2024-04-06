import argparse

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    ExitProgramReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_info

client_sessions_service = client_singletons.client_sessions_service


class ExitCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="exit",
            description="Exit the Consortium client.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    exit  # Exit the Consortium client.
                """,
            ),
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ExitProgramReturnStatus | ContinueReturnStatus:
        try:
            _ = self._parser.parse_args(interpreter_command.arguments)

            for client_session in client_sessions_service.get_all_client_sessions():
                await client_session.logout()
                client_sessions_service.remove_client_session(client_session)

            print_info("Exiting...")
            return ExitProgramReturnStatus()
        except SystemExit:
            return ContinueReturnStatus()

import argparse
from typing import Type

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
        client_session: ClientSession | None,
        interpreter: Type[BaseInterpreter],
    ) -> ExitProgramReturnStatus | ContinueReturnStatus:
        try:
            _ = self._parser.parse_args(interpreter_command.arguments)
            print_info("Exiting...")
            return ExitProgramReturnStatus()
        except SystemExit:
            return ContinueReturnStatus()

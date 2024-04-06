import argparse

from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
    SwitchInterpreterReturnStatus,
)
from consortium.client.objects.interpreter_objects import InterpreterType
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_info


class GeneratorsCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Switch to the generators interpreter.",
            prog="generators",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    generators  # Switch to the generators interpreter.
                """,
            ),
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> SwitchInterpreterReturnStatus | ContinueReturnStatus:
        try:
            _ = self._parser.parse_args(interpreter_command.arguments)
            print_info("Switching to generators interpreter...")
            return SwitchInterpreterReturnStatus(
                interpreter_type=InterpreterType.GENERATORS,
            )
        except SystemExit:
            return ContinueReturnStatus()

import argparse
import platform
import subprocess
from typing import Type

from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter


class ClearCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="clear",
            description="Clear the terminal screen.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    clear  # Clear the terminal screen.

                """,
            ),
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None,
        interpreter: Type[BaseInterpreter],
    ) -> ContinueReturnStatus:
        try:
            _ = self._parser.parse_args(interpreter_command.arguments)
            if platform.system() == "Windows":
                subprocess.run("cls", shell=True)
            # platform.system returns "Darwin" for macOS and "Linux" for nix systems.
            else:
                subprocess.run("clear", shell=True)
        except SystemExit:
            pass

        return ContinueReturnStatus()

import argparse
import subprocess

from consortium.client.models.context_models import AnyContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ExecCommand(BaseCommand[AnyContext]):
    name = "exec"
    description = "Execute a command in the system shell"
    epilog = format_argparse_epilog(
        """
        Examples:
          exec echo Hello, world!
          exec python --version

        Note:
          Everything after 'exec' is passed directly to the system shell, so the
          command does not need to be enclosed in quotes.
        """,
    )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "shell_command",
            nargs=argparse.REMAINDER,
            help="The command to execute in the system shell.",
        )

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            if not parsed_args.shell_command:
                self.parser.error("the following arguments are required: shell_command")

            # shell_command = context.raw_input.split(maxsplit=1)[1]
            subprocess.run(parsed_args.shell_command, shell=True)
        except SystemExit:
            pass

        return ContinueSignal()

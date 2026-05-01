import argparse

from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class RCCommand(BaseCommand):
    name = "rc"
    description = (
        "Run commands from a provided resource file in the current interpreter"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          rc resource_file.txt

        Note:
          Resource files should contain one command per line. Lines starting with '#'
          are treated as comments and ignored.
        """,
    )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "resource_file",
            nargs="?",
            help="File path of the resource file to run commands from.",
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            try:
                with open(parsed_args.resource_file) as f:
                    commands = [  # noqa
                        line
                        for line in f.read().splitlines()
                        if line and not line.startswith("#")
                    ]
                    print_info(f"Loaded resource file: {parsed_args.resource_file}")
            except Exception as exc:
                print_info(f"Failed to read resource file: {exc}")
        except SystemExit:
            pass

        return ContinueSignal()

import argparse

from consortium.client.models.context_models import AnyContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class RcCommand(BaseCommand):
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

          Commands ran from a resource file will have the prompt prefixed with `[RC]`
          to indicate them appropriately.
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
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            resource_file = parsed_args.resource_file

            try:
                with open(resource_file) as f:
                    commands = [
                        line
                        for line in f.read().splitlines()
                        if line and not line.startswith("#")
                    ]
                    for command in commands:
                        context.interpreter_context["resource_commands"].append(command)
                    print_info(f"Loaded resource file: {resource_file}")
            except Exception as exc:
                print_info(f"Failed to read resource file '{resource_file}' : {exc}")
        except SystemExit:
            pass

        return ContinueSignal()

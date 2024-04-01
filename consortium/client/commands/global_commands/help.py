import argparse
from typing import Type

from rich.console import Console
from rich.table import Table

from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error, print_plain


class HelpCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Get a summary for a command or display the help menu for all available commands.",
            prog="help",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    help  # Display the help menu for all available commands.
                    help local  # Display the help page for the local command.
                    help banner  # Display the help page for the banner command.
                """,
            ),
        )
        parser.add_argument("command", help="command to get help for", nargs="?")
        super().__init__(parser)

    @staticmethod
    def _print_summarized_help_menu(
        interpreter: Type[BaseInterpreter],
    ) -> None:
        table = Table(title="Commands")
        table.add_column("Command")
        table.add_column("Description")

        help_menu_entries = []
        for _, command in sorted(interpreter.commands.items()):
            help_menu_entries.append([command.name, command.description])

        for command, description in help_menu_entries:
            table.add_row(command, description)

        Console().print(table)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None,
        interpreter: Type[BaseInterpreter],
    ) -> ContinueReturnStatus:
        try:
            parsed_args = self._parser.parse_args(
                interpreter_command.arguments,
            )
            if parsed_args.command:
                if parsed_args.command in interpreter.commands:
                    print_plain(
                        interpreter.commands[parsed_args.command].summary,
                    )
                else:
                    print_error(f"Invalid command: {parsed_args.command}")
            else:
                self._print_summarized_help_menu(interpreter)
        except SystemExit:
            pass

        return ContinueReturnStatus()

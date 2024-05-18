import argparse

from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE, print_error


class HelpCommand(BaseCommand):
    name = "help"
    description = (
        "Display the help summary of a specific command or display the help menu "
        "listing all available commands for the current interpreter."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            help  # Displays the help menu listing all available commands if no command name is specified.
            help banner
        """,
    )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "command_name",
            nargs="?",
            help="The name of the command to display the help summary for.",
        )

    @staticmethod
    def _print_summarized_help_menu(commands: dict[str, BaseCommand]) -> None:
        table = Table(title="Help Menu")
        table.add_column("Command")
        table.add_column("Description")

        help_menu_entries = []
        for _, command in sorted(commands.items()):
            help_menu_entries.append([command.name, command.description])

        for command, description in help_menu_entries:
            table.add_row(command, description)

        CONSOLE.print(table)

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(
                command_context.arguments,
            )

            if parsed_args.command_name:
                if parsed_args.command_name in command_context.environment["commands"]:
                    print(
                        command_context.environment["commands"][
                            parsed_args.command_name
                        ].summary,
                    )
                else:
                    print_error(f"Invalid command: {parsed_args.command_name}")
            else:
                self._print_summarized_help_menu(
                    command_context.environment["commands"],
                )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )

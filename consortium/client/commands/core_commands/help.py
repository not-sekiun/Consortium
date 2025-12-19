import argparse

from rich.table import Table

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
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
        command_groups = {}
        command_col_width = max(len(command.name) for command in commands.values())
        max_description_length = max(
            len(command.description) for command in commands.values()
        )
        # Command column has 4 characters of padding, table borders and space.
        # Description column has 3 characters of padding, space on left and space and
        # border on right.
        padding_width = 7
        description_col_width = min(
            max_description_length, CONSOLE.width - command_col_width - padding_width
        )

        # Group commands by their specified group or default to "General Commands"
        for _, command in commands.items():
            # "General Commands" is the default group if no group is specified
            group = command.group or "General Commands"
            if group not in command_groups:
                command_groups[group] = [command]
            else:
                command_groups[group].append(command)

        # Sort the command groups and iterate over them to print each group table
        for group_name, group_commands in dict(sorted(command_groups.items())).items():
            table = Table(title=group_name)
            table.add_column("Command", width=command_col_width)
            table.add_column("Description", width=description_col_width)
            # Sort each group's commands by name before adding to the table
            for command in sorted(group_commands, key=lambda command: command.name):
                table.add_row(command.name, command.description)
            CONSOLE.print(table)
            print()

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

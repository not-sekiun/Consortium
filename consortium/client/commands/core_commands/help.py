import argparse

from rich.table import Table

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import console, print_error


class HelpCommand(BaseCommand):
    name = "help"
    description = (
        "Display help menu for the current interpreter, or for a specific command"
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
            help="Name of the command to display the help summary for.",
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
            max_description_length, console.width - command_col_width - padding_width
        )

        # Group commands by their specified group or default to "General Commands"
        for _, command in commands.items():
            # "General Commands" is the default group if no group is specified
            group = command.group or "General Commands"
            if group not in command_groups:
                command_groups[group] = [command]
            else:
                command_groups[group].append(command)

        # If agent capability commands exist, remove them from the set of command
        # groups. We want to print them in a separate section at the end with its own
        # style
        agent_capability_commands = command_groups.get("Agent Capability Commands")
        if agent_capability_commands is not None:
            del command_groups["Agent Capability Commands"]

        # Sort the command groups and iterate over them to print each group table
        for group_name, group_commands in dict(sorted(command_groups.items())).items():
            table = Table(title=group_name)
            table.add_column("Command", width=command_col_width)
            table.add_column("Description", width=description_col_width)
            # Sort each group's commands by name before adding to the table
            for command in sorted(group_commands, key=lambda command: command.name):
                table.add_row(command.name, command.description)
            console.print(table, "")

        # If agent capability commands exist, print them in a separate section with
        # their own style
        if agent_capability_commands is not None:
            table = Table(
                title="Agent Capability Commands", title_style="italic bold magenta"
            )
            table.add_column("Command", width=command_col_width, style="bold magenta")
            table.add_column("Description", width=description_col_width)
            for command in sorted(
                agent_capability_commands, key=lambda command: command.name
            ):
                table.add_row(command.name, command.description)
            console.print(table, "")

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(
                context.arguments,
            )

            if parsed_args.command_name:
                if parsed_args.command_name in context.environment["commands"]:
                    print(
                        context.environment["commands"][
                            parsed_args.command_name
                        ].summary,
                    )
                else:
                    print_error(f"Invalid command: {parsed_args.command_name}")
            else:
                self._print_summarized_help_menu(
                    context.environment["commands"],
                )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )

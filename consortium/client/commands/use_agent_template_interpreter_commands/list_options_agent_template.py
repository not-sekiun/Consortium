from argparse import ArgumentParser

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
from consortium.client.utils.printer_utils import CONSOLE


class ListOptionsAgentTemplateCommand(BaseCommand):
    name = "list_options_agent_template"
    description = (
        "List all options for the currently selected agent template being used."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          list_options_agent_template
        """,
    )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)

            table = Table(title="Agent Template Options")
            table.add_column("Option Type")
            table.add_column("Name")
            table.add_column("Description")
            table.add_column("Required")
            table.add_column("Current Value")
            for option_name, option in command_context.environment["agent_template"][
                "options"
            ].items():
                table.add_row(
                    option["option_type"],
                    option_name,
                    option["description"],
                    str(option["required"]),
                    str(option["value"]) if option["value"] is not None else "",
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )

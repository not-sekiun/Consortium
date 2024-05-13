from argparse import ArgumentParser

from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_listener_state_string_with_color,
)
from consortium.client.utils.printer_utils import CONSOLE


class InfoAgentCommand(BaseCommand):
    name = "info_agent"
    description = (
        "Display detailed information about a specific agent or for the currently "
        "selected agent being interacted with."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            info_agent 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to display detailed information for.",
            nargs="?",
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]

            if parsed_args.listener_template_id is None:
                agent = command_context.environment["agent"]
            else:
                agent = await client_connection.get_agent_by_agent_id(
                    parsed_args.agent_id,
                )

            table = Table(title="Agent Information")
            table.add_column("Information")
            table.add_column("Data")
            table.add_row(
                "Agent ID",
                agent["agent_id"],
            )
            table.add_row("Name", agent["name"])
            table.add_row("Description", agent["description"])

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )

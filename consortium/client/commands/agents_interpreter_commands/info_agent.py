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
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE


class InfoAgentCommand(BaseCommand):
    name = "info_agent"
    description = "Display detailed information about a specific agent."
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
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]
            agent = await client_connection.get_agent_by_agent_id(
                parsed_args.agent_id[0],
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
            table.add_row("Endpoint", agent["endpoint"])
            agent_data_table = Table(title="Agent Data")
            agent_data_table.add_column("Information")
            agent_data_table.add_column("Data")
            for key, value in agent["agent_data"].items():
                agent_data_table.add_row(key, value)
            table.add_row("Agent Data", agent_data_table)
            # # TODO: Figure out a standardized way to represent and print results
            # table.add_row("Results", repr(agent["results"]))
            table.add_row(
                "Datetime First Checked In",
                agent["datetime_first_checked_in"],
            )
            table.add_row("Datetime Last Checked In", agent["datetime_last_checked_in"])

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )

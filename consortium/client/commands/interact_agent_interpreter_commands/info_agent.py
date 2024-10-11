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
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]

            if parsed_args.agent_id is None:
                agent = command_context.environment["agent"]
            else:
                agent = await client_rest_api_connection.get_agent_by_agent_id(
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
            table.add_row("Endpoint", agent["endpoint"])
            agent_type_table = Table()
            agent_type_table.add_column("Information")
            agent_type_table.add_column("Data")
            agent_type_table.add_row(
                "Agent Type ID",
                agent["agent_type"]["agent_type_id"],
            )
            agent_type_table.add_row(
                "Name",
                agent["agent_type"]["name"],
            )
            agent_type_table.add_row(
                "Compatible Listener Types",
                "\n".join(
                    [
                        listener_type["name"]
                        + " ("
                        + listener_type["listener_type_id"]
                        + ")"
                        for listener_type in agent["agent_type"][
                            "compatible_listener_types"
                        ]
                    ],
                ),
            )
            table.add_row("Agent Type", agent_type_table)
            table.add_row("Running As Admin", agent["is_admin"])
            table.add_row("Operating System", agent["os"])
            table.add_row("System Version", agent["version"])
            table.add_row("System Arch", agent["arch"])
            table.add_row("Process ID", agent["pid"])
            table.add_row("System Locale", agent["locale"])
            table.add_row("Remote Host Address", agent["remote_host_address"])
            table.add_row("Local Host Address", agent["local_host_address"])
            table.add_row("First Checked In", agent["datetime_first_checked_in"])
            table.add_row("Last Checked In", agent["datetime_last_checked_in"])
            agent_data_table = Table(title="Agent Data")
            agent_data_table.add_column("Information")
            agent_data_table.add_column("Data")
            for key, value in agent["agent_data"].items():
                agent_data_table.add_row(key, value)
            table.add_row("Agent Data", agent_data_table)

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )

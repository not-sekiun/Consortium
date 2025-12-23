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
    description = "Display detailed information about a specific agent."
    epilog = format_argparse_epilog(
        """
        Examples:
          info_agent 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to display detailed information for.",
            nargs=1,
        )

    @staticmethod
    def _display_agent_info(
        agent: dict,
    ) -> None:
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
        table.add_row("Agent Type", agent["agent_type"]["name"])
        table.add_row(
            "Agent Capabilities",
            "\n".join(list(agent["agent_type"]["agent_capabilities"])),
        )
        table.add_row("Running As Admin", str(agent["is_admin"]))
        table.add_row("Operating System", agent["os"])
        table.add_row("System Version", agent["version"])
        table.add_row("System Arch", agent["arch"])
        table.add_row("Process ID", str(agent["pid"]))
        table.add_row("System Locale", agent["locale"])
        table.add_row("Remote Host Address", agent["remote_host_address"])
        table.add_row("Local Host Address", agent["local_host_address"])
        table.add_row("First Checked In", agent["datetime_first_checked_in"])
        table.add_row("Last Checked In", agent["datetime_last_checked_in"])
        agent_data_table = Table()
        agent_data_table.add_column("Information")
        agent_data_table.add_column("Data")
        for key, value in agent["agent_data"].items():
            agent_data_table.add_row(key, str(value))
        table.add_row("Agent Data", agent_data_table)

        CONSOLE.print(table)

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            agent = await client_rest_api_connection.get_agent_by_agent_id(
                agent_id=parsed_args.agent_id[0]
            )
            self._display_agent_info(agent=agent)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

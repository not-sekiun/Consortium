from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
)
from consortium.client.utils.printer_utils import console


class AgentInfoCommand(BaseCommand):
    name = "info"
    description = "Display information about an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent to display information for.",
            nargs=1,
        )

    @staticmethod
    async def _display_agent_info(
        rest_api: RestAPI,
        agent_id: str,
    ) -> None:
        agent = await rest_api.get_agent_by_agent_id(
            agent_id=agent_id,
        )
        table = Table(title="Agent Information", highlight=True)
        table.add_column("Information")
        table.add_column("Data")
        table.add_row(
            "Agent ID",
            agent["agent_id"],
        )
        table.add_row("Name", str(agent["name"]))
        table.add_row("Description", str(agent["description"]))
        table.add_row("Endpoint", str(agent["endpoint"]))
        table.add_row("Agent Type", str(agent["agent_type"]["name"]))
        table.add_row(
            "Agent Capabilities",
            format_dict_as_multi_line_key_value_string(
                input_dict={
                    name: capability["description"]
                    for name, capability in agent["agent_type"][
                        "agent_capabilities"
                    ].items()
                },
                display_value_as_repr=False,
            ),
        )
        table.add_row("User", str(agent["user"]))
        table.add_row("Running As Admin", str(agent["is_admin"]))
        table.add_row("Operating System", str(agent["os"]))
        table.add_row("System Version", str(agent["version"]))
        table.add_row("System Arch", str(agent["arch"]))
        table.add_row("Process ID", str(agent["pid"]))
        table.add_row("System Locale", str(agent["locale"]))
        table.add_row("Remote Host Address", str(agent["remote_host_address"]))
        table.add_row("Local Host Address", str(agent["local_host_address"]))
        table.add_row(
            "First Checked In",
            format_datetime_as_human_readable_str(
                datetime_str=agent["datetime_first_checked_in"],
                include_elapsed_time=True,
            ),
        )
        table.add_row(
            "Last Checked In",
            format_datetime_as_human_readable_str(
                datetime_str=agent["datetime_last_checked_in"],
                include_elapsed_time=True,
            ),
        )
        table.add_row(
            "Agent Data",
            format_dict_as_multi_line_key_value_string(agent["agent_data"]),
        )

        console.print(table, "")

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._display_agent_info(
                rest_api=rest_api, agent_id=parsed_args.agent_id[0]
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)

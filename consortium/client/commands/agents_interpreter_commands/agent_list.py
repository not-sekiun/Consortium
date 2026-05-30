from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.formatter_utils import (
    format_agent_status_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class AgentListCommand(BaseCommand[ConnectedContext]):
    name = "list"
    description = "List all agents along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          list
        """,
    )
    group = "Agent Management Commands"

    @staticmethod
    def _list_all_agents(
        all_agents: list[dict],
    ) -> None:
        table = Table(title="Agents", highlight=True)
        table.add_column("Agent ID")
        table.add_column("Agent Type")
        table.add_column("Name")
        table.add_column("Endpoint")
        table.add_column("Last Checked In")
        table.add_column("Status")
        for agent in all_agents:
            table.add_row(
                str(agent["agent_id"]),
                str(agent["agent_type"]["name"]),
                str(agent["name"]),
                str(agent["endpoint"]),
                format_datetime_as_human_readable_str(
                    agent["datetime_last_checked_in"], include_elapsed_time=True
                ),
                format_agent_status_string_with_color(
                    status_str=agent["status"],
                ),
            )
        console.print(table, "")

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            self._list_all_agents(all_agents=await rest_api.get_all_agents())
        except SystemExit:
            pass

        return ContinueSignal()

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


class ListAgentsCommand(BaseCommand):
    name = "list_agents"
    description = "List all connected agents along with their essential information."
    epilog = format_argparse_epilog(
        """
        Examples:
            list_agents
        """,
    )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]
            all_agents = await client_connection.get_all_agents()

            table = Table(title="Agents")
            table.add_column("Agent ID")
            table.add_column("Name")
            for agent in all_agents:
                table.add_row(
                    agent["agent_id"],
                    agent["name"],
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

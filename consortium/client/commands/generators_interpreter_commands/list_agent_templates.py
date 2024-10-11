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


class ListAgentTemplatesCommand(BaseCommand):
    name = "list_agent_templates"
    description = "List all available agent templates for reference and selection."
    epilog = format_argparse_epilog(
        """
        Examples:
          list_agent_templates
        """,
    )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            all_agent_templates = (
                await client_rest_api_connection.get_all_agent_templates()
            )

            table = Table(title="Agent Templates")
            table.add_column("Agent Template ID")
            table.add_column("Name")
            for agent_template in all_agent_templates:
                table.add_row(
                    agent_template["agent_template_id"],
                    agent_template["name"],
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

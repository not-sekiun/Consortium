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
from consortium.client.utils.printer_utils import console


class ListAgentTemplatesCommand(BaseCommand):
    name = "list_agent_templates"
    description = "List all available agent templates for reference and selection."
    epilog = format_argparse_epilog(
        """
        Examples:
          list_agent_templates
        """,
    )
    group = "Agent Template Management Commands"

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            client_rest_api_connection = context.client_session.rest_api
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

            console.print(table, "")
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)

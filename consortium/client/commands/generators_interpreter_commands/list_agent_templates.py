from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import CONSOLE
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class ListAgentTemplatesCommand(BaseCommand):
    name = "list_agent_templates"
    description = "List all agent templates."
    epilog = argparse_epilog_formatter(
        """
        Example:
            list_agent_templates  # List all agent templates
        """,
    )

    def configure_parser(self, parser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            all_agent_templates = await command_context.environment[
                "client_connection"
            ].get_all_agent_templates()

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

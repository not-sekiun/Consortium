from rich.table import Table

import consortium.client.client_singletons as client_singletons
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


class ListListenerTemplatesCommand(BaseCommand):
    name = "list_listener_templates"
    description = "List all listener templates."
    epilog = format_argparse_epilog(
        """
        Example:
            list_listener_templates  # List all listener templates
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
            all_listener_templates = await command_context.environment[
                "client_connection"
            ].get_all_listener_templates()

            table = Table(title="Listener Templates")

            table.add_column("Listener Template ID")
            table.add_column("Name")

            for listener_template in all_listener_templates:
                table.add_row(
                    listener_template["listener_template_id"],
                    listener_template["name"],
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

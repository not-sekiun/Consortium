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


class ListenerTemplateListCommand(BaseCommand):
    name = "lt-list"
    description = "List all listener templates along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          lt-list
        """,
    )
    group = "Listener Template Management Commands"

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            all_listener_templates = await rest_api.get_all_listener_templates()
            table = Table(title="Listener Templates", highlight=True)
            table.add_column("Listener Template ID")
            table.add_column("Listener Type")
            table.add_column("Name")
            for listener_template in all_listener_templates:
                table.add_row(
                    listener_template["listener_template_id"],
                    listener_template["listener_type"]["name"],
                    listener_template["name"],
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)

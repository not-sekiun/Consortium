from rich.table import Table

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
    format_listener_state_string_with_color,
)
from consortium.client.utils.printer_utils import console


class ListenerListCommand(BaseCommand):
    name = "list"
    description = "List all listeners along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          list
        """,
    )
    group = "Listener Management Commands"

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            all_listeners = await rest_api.get_all_listeners()
            table = Table(title="Listeners", highlight=True)
            table.add_column("Listener ID")
            table.add_column("Listener Type")
            table.add_column("Name")
            table.add_column("Endpoint")
            table.add_column("Status")
            for listener in all_listeners:
                table.add_row(
                    listener["listener_id"],
                    listener["listener_type"]["name"],
                    listener["name"],
                    listener["endpoint"],
                    format_listener_state_string_with_color(
                        listener["status"]["state"],
                    ),
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)

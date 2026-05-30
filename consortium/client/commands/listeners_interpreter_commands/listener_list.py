from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_listener_state_string_with_color,
)
from consortium.client.utils.printer_utils import console


class ListenerListCommand(BaseConnectedCommand):
    name = "list"
    description = "List all listeners along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          list
        """,
    )
    group = "Listener Management Commands"

    @staticmethod
    def _list_all_listeners(
        all_listeners: list[dict],
    ):
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

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            self._list_all_listeners(all_listeners=await rest_api.get_all_listeners())
        except SystemExit:
            pass

        return ContinueSignal()

from typing import Any

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import console


class ListenerTemplateListCommand(BaseConnectedCommand):
    name = "lt-list"
    description = "List all listener templates along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          lt-list
        """,
    )
    group = "Listener Template Management Commands"

    @staticmethod
    def _list_all_listener_templates(
        all_listener_templates: list[dict[str, Any]],
    ) -> None:
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

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            self._list_all_listener_templates(
                all_listener_templates=await rest_api.get_all_listener_templates()
            )
        except SystemExit:
            pass

        return ContinueSignal()

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class PayloadListCommand(BaseConnectedCommand):
    name = "pl-list"
    description = "List all payloads along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          pl-list
        """,
    )
    group = "Payload Management Commands"

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            payloads = await rest_api.get_all_payloads()

            table = Table(title="Payloads", highlight=True)
            table.add_column("Resource ID")
            table.add_column("Name")
            table.add_column("Agent Type")
            table.add_column("Type")
            table.add_column("Size")
            for payload in payloads:
                size = payload["size"]
                table.add_row(
                    payload["resource_id"],
                    payload["name"],
                    payload["agent_type"]["name"],
                    "DIRECTORY" if payload["is_directory"] else "FILE",
                    format_size_bytes_as_human_readable_str(size_bytes=size)
                    if size is not None
                    else "N/A",
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()

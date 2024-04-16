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
from consortium.client.utils.printer_utils import CONSOLE
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter

client_connections_service = client_singletons.client_connections_service


class ListListenersCommand(BaseCommand):
    name = "list_listeners"
    description = "List all listeners."
    epilog = argparse_epilog_formatter(
        """
        Example:
            list_listeners  # List all listeners
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
            all_listeners = await command_context.environment[
                "client_connection"
            ].get_all_listeners()

            table = Table(title="Listeners")

            table.add_column("Listener ID")
            table.add_column("Name")

            for listener in all_listeners:
                table.add_row(
                    listener["listener_id"],
                    listener["name"],
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

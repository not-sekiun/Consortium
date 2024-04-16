import argparse

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


class ListClientConnectionsCommand(BaseCommand):
    name = "list_client_connections"
    description = "List all current client connections."
    epilog = argparse_epilog_formatter(
        """
        Example:
            list_client_connections  # List all current client connections
        """,
    )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            all_client_sessions = (
                client_connections_service.get_all_client_connections()
            )
            table = Table(title="Client Connections")

            table.add_column("Client Connection ID")
            table.add_column("Name")

            for client_session in all_client_sessions:
                table.add_row(
                    str(client_session.client_connection_id),
                    client_session.name,
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
